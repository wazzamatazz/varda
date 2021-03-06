import hashlib
import json
import logging
import re
from collections import Counter

import requests
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from time import sleep

from varda.models import Henkilo
from varda.oph_yhteiskayttopalvelu_autentikaatio import get_authentication_header, get_contenttype_header

# Get an instance of a logger
logger = logging.getLogger(__name__)


class CustomServerErrorException(APIException):
    default_detail = "A server error occurred. Team is investigating this."


def sleep_if_not_test(x_seconds):
    if not settings.TESTING:
        sleep(x_seconds)


def hash_string(string):
    """
    Return a SHA-256 hash of the given string
    """
    return hashlib.sha256(string.encode('utf-8')).hexdigest()


def decrypt_henkilotunnus(encrypted_henkilotunnus):
    """
    This is needed when updating henkilo-data from Oppijanumerorekisteri.

    Original key generated with: Fernet.generate_key().decode('utf-8')
    Details: https://cryptography.io/en/latest/fernet/
    """
    f = _get_fernet()

    try:
        resolved_token = f.decrypt(encrypted_henkilotunnus.encode('utf-8'))
    except TypeError:
        logger.error("Decrypt henkilotunnus: Fernet token is not bytes.")
        raise CustomServerErrorException
    except InvalidToken:
        logger.error("Decrypt henkilotunnus: Invalid token.")
        raise CustomServerErrorException
    return resolved_token.decode('utf-8')  # convert bytes -> string


def _get_fernet():
    decoded_key = settings.FERNET_SECRET_KEY
    key = decoded_key.encode('utf-8')
    if not key:
        logger.error("Henkilotunnus decryption failed. No secret key available.")
        raise CustomServerErrorException
    return Fernet(key)


def encrypt_henkilotunnus(henkilotunnus):
    f = _get_fernet()

    try:
        token = f.encrypt(henkilotunnus.encode('utf-8'))
    except TypeError:
        logger.error("Encrypt henkilotunnus: Data is not bytes.")
        raise CustomServerErrorException
    return token.decode('utf-8')  # convert bytes -> string


@transaction.atomic
def rotate_henkilotunnus(henkilo_id, f=None):
    henkilo = Henkilo.objects.get(id=henkilo_id)
    try:
        henkilotunnus_encrypted = henkilo.henkilotunnus.encode('utf-8')
        if henkilotunnus_encrypted != b'':
            if not f:
                f = _get_fernet()
            henkilo.henkilotunnus = f.rotate(henkilotunnus_encrypted).decode('utf-8')
            henkilo.save()
    except TypeError:
        logger.error('Hetu invalid format. Expecting bytes.')


def get_reply_json(is_ok, json_msg=None):
    return {"is_ok": is_ok, "json_msg": json_msg}


def decode_json_msg(reply_type, response, service_name):
    try:
        if reply_type == 'json':
            json_msg = json.loads(response.content)
        elif reply_type == 'text':
            json_msg = response.text
        else:
            raise ValueError('Illegal argument {}'.format(reply_type))
    except json.JSONDecodeError:
        logger.error(service_name + ': Could not decode json. Invalid reply.')
        return None
    return json_msg


def send_request_get_response(service_name, http_url_suffix, headers, request_type, data_json, large_query):
    """
    Request timeout: https://requests.readthedocs.io/en/master/user/advanced/#timeouts
    """
    DEFAULT_CONNECT_TIMEOUT = 7  # seconds
    DEFAULT_READ_TIMEOUT = 15    # seconds
    DEFAULT_READ_TIMEOUT_LARGE_QUERY = 3600  # seconds
    if large_query:
        DEFAULT_TIMEOUT_TUPLE = (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT_LARGE_QUERY)
    else:
        DEFAULT_TIMEOUT_TUPLE = (DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT)
    response = None

    try:
        http_complete_url = settings.OPINTOPOLKU_DOMAIN + "/" + service_name + http_url_suffix
        if request_type == 'get':
            response = requests.get(http_complete_url, headers=headers, timeout=DEFAULT_TIMEOUT_TUPLE)
        elif request_type == 'post':
            response = requests.post(http_complete_url, headers=headers, data=data_json, timeout=DEFAULT_TIMEOUT_TUPLE)
        else:  # put
            response = requests.put(http_complete_url, headers=headers, data=data_json, timeout=DEFAULT_TIMEOUT_TUPLE)
    except requests.exceptions.RequestException as e:
        logger.error(e)
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
    except requests.exceptions.Timeout as e:
        logger.error(e)

    return response


def send_request_to_external_service(request_type, service_name, http_url_suffix, expected_status_code, auth,
                                     reply_type='json', data_json=None, large_query=False):
    """
    Response.close():
    https://github.com/psf/requests/blob/a9ee0eef5a70acb9ed35622b3675574b11f92cb4/requests/models.py#L963
    """
    MAX_NO_OF_ATTEMPS = 3
    number_of_attempt = 0
    while number_of_attempt < MAX_NO_OF_ATTEMPS:
        number_of_attempt += 1
        headers = get_authentication_header(service_name, external_request=False) if auth else get_contenttype_header()
        response = send_request_get_response(service_name, http_url_suffix, headers, request_type, data_json, large_query)
        if response is None:
            logger.error('Could not get a response: {}, {}, {}'.format(request_type, service_name, http_url_suffix))
            sleep_if_not_test(2)
            continue

        if response.status_code == expected_status_code:
            pass
        elif response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]:
            url_possible_hetu_hidden = hide_hetu(service_name + http_url_suffix)
            logger.error('{}: Authentication issue. Status_code: {}. Url: {}. Service-ticket: {}.'
                         .format(service_name, response.status_code, url_possible_hetu_hidden, headers['CasSecurityTicket']))
            response.close()
            sleep_if_not_test(2)
            continue
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            break
        else:
            logger.error('{0}: {1}-request ({0}{2}) returned status_code: {3}, {4}'
                         .format(service_name, request_type, http_url_suffix, response.status_code, response.content))
            response.close()
            sleep_if_not_test(2)
            continue

        json_msg = decode_json_msg(reply_type, response, service_name)
        if json_msg is None:
            logger.error('Could not get a valid json_msg: {}, {}, {}'.format(request_type, service_name, http_url_suffix))
            response.close()
            sleep_if_not_test(2)
            continue

        return get_reply_json(is_ok=True, json_msg=json_msg)
    return get_reply_json(is_ok=False)


def get_json_from_external_service(service_name, http_url_suffix, auth=True, large_query=False):
    request_type = 'get'
    expected_status_code = status.HTTP_200_OK
    return send_request_to_external_service(request_type, service_name, http_url_suffix, expected_status_code, auth,
                                            large_query=large_query)


def post_json_to_external_service(service_name, http_url_suffix, data_json, expected_status_code, auth=True,
                                  reply_type='json'):
    request_type = 'post'
    return send_request_to_external_service(request_type, service_name, http_url_suffix, expected_status_code, auth,
                                            reply_type=reply_type, data_json=data_json)


def put_json_to_external_service(service_name, http_url_suffix, data_json, expected_status_code):
    request_type = 'put'
    auth = True
    return send_request_to_external_service(request_type, service_name, http_url_suffix, expected_status_code, auth,
                                            data_json=data_json)


def get_object_id_from_path(request_path):
    """
    Parse object-id from request path. Eg.
    ['', 'api', 'v1', 'varhaiskasvatuspaatokset', '1', '']  --->  return 1
    """
    splitted_path = request_path.split('/')
    if len(splitted_path) != 6:
        logger.error('request_path length invalid. Path: ' + request_path)
        return None
    object_id = splitted_path[4]
    if not object_id.isdigit():
        return None
    return object_id


def list_to_chunks(list_, size):
    return [list_[i:i + size] for i in range(0, len(list_), size)]


def intersection(lst1, lst2):
    """
    TODO: Perfect place for C-extension (=speedup!)
    """
    return sorted(list(set(lst1) & set(lst2)))


def hide_hetu(string):
    hetu_regex = re.compile('\\d{6}([A+\\-]\\d{3}[0-9A-FHJ-NPR-Y])')
    if string:
        if not isinstance(string, str):
            string = str(string)
        if re.search(hetu_regex, string):
            return re.sub(hetu_regex, r'DDMMYY\1', string)
    return string


def list_of_dicts_has_duplicate_values(searchable_list, key_name):
    """
    https://www.robjwells.com/2015/08/python-counter-gotcha-with-max/
    """
    c = Counter()
    for item in searchable_list:
        if key_name in item:
            c[item[key_name]] += 1

    highest_occurrence = c.most_common(1)[0][1] if c else None
    if highest_occurrence is not None and highest_occurrence > 1:
        return True
    return False


def test_decrypt_all_hetus():
    """
    Validate all hetus in db are decryptable. Meant to be run after after fernet key rotation.
    """
    logger.info("Starting decrypting all hetus in db")
    [decrypt_henkilotunnus(henkilotunnus) for henkilotunnus in Henkilo.objects.exclude(henkilotunnus='').values_list('henkilotunnus', flat=True)]
    logger.info("Finished decrypting all hetus in db succesfully")
