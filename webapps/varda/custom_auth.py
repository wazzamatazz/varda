from __future__ import unicode_literals

import json
import logging
import os
import requests
import uuid

from datetime import datetime, timedelta, timezone
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils.translation import ugettext_lazy as _
from django_cas_ng.signals import cas_user_logout
from rest_framework import exceptions
from rest_framework.authentication import BasicAuthentication
from rest_framework.authtoken.models import Token

from varda import kayttooikeuspalvelu
from varda.clients.organisaatio_client import organization_is_not_active_vaka_organization
from varda.oph_yhteiskayttopalvelu_autentikaatio import get_authentication_header
from varda.models import VakaJarjestaja, Z3_AdditionalCasUserFields, Z4_CasKayttoOikeudet, Huoltajuussuhde
from varda.permission_groups import get_permission_group
from varda.organisaatiopalvelu import create_vakajarjestaja_using_oid
from webapps.celery import app
from celery.signals import task_prerun
from log_request_id import local


# Get an instance of a logger
logger = logging.getLogger(__name__)


def login_handler(sender, user, request, **kwargs):
    """
    Actions to be performed for the logged in user:
    - We need to check the user permissions for each non-local user explicitly from Kayttooikeuspalvelu.
    """
    if request.method == 'GET':  # GET-request means CAS / POST-request '/api-auth/login/' would mean local account.
        if request.resolver_match.view_name == 'oppija_cas_ng_login':
            _oppija_post_login_handler(user)
        else:
            kayttooikeuspalvelu.set_permissions_for_cas_user(user.id)


def _oppija_post_login_handler(user):
    """
    Handles oppija cas logged in user privileges givin parent
    :param user:
    :return:
    """
    if not hasattr(user, 'personOid') or not hasattr(user, 'impersonatorPersonOid'):
        raise ValueError('User %s missing required argument personOid or impersonatorPersonOid received from CAS'
                         .format(user.username))
    lapsi_oid = user.personOid
    huoltaja_oid = user.impersonatorPersonOid
    huoltajuussuhteet = (Huoltajuussuhde.objects
                         .filter(lapsi__henkilo__henkilo_oid=lapsi_oid,
                                 huoltaja__henkilo__henkilo_oid=huoltaja_oid,
                                 voimassa_kytkin=True))
    # Check active parent relation exists before adding any privileges
    if len(huoltajuussuhteet) > 0:
        Z3_AdditionalCasUserFields.objects.update_or_create(user=user,
                                                            defaults={
                                                                "henkilo_oid": lapsi_oid,
                                                                "huoltaja_oid": huoltaja_oid,
                                                            })
    else:
        Z3_AdditionalCasUserFields.objects.filter(user=user, henkilo_oid=lapsi_oid, huoltaja_oid=huoltaja_oid).delete()


def logout_handler(sender, user, request, **kwargs):
    """
    user - The user instance that just logged out or None if the user was not authenticated.

    Actions to be performed for the logged out user:
    - We need to delete the auth-token from the user.
    """
    if user is not None:
        Token.objects.get_or_create(user=user)[0].delete()


def cas_logout_handler(sender, user, session, ticket, **kwargs):
    if user is None or user.is_anonymous:
        pass
    else:
        Token.objects.get_or_create(user=user)[0].delete()


def celery_task_prerun_signal_handler(task_id, **kwargs):
    """
    Check for periodic tasks: we want to run periodic task only for varda-0 POD.
    See Kubernetes Statefulesets for more information.
    Additionally: New request_id for celery tasks from celery task_id.
    """
    splitted_hostname = os.environ["HOSTNAME"].split("-")
    if len(splitted_hostname) == 2:
        hostname = splitted_hostname[1]  # e.g. varda-0 --> 0
    else:
        hostname = None

    local.request_id = task_id.replace("-", "")
    if 'periodic_task' in kwargs and kwargs['periodic_task'] and hostname != "0":
        """
        If not the first (0) POD, cancel periodic task

        TODO: Seems like revoking is currently not working: https://github.com/celery/celery/issues/4300
        However, this is not a huge deal, since we stop running the task for others than pod-0.
        """
        app.control.revoke(task_id)


# Catch signals
user_logged_in.connect(login_handler)
user_logged_out.connect(logout_handler)
cas_user_logout.connect(cas_logout_handler)
task_prerun.connect(celery_task_prerun_signal_handler)


class CustomBasicAuthentication(BasicAuthentication):
    """
    Custom: allow basic authentication only for fetching token (apikey)
    This is used ONLY for palvelukayttaja-authentication.
    """
    def authenticate_and_get_omattiedot(self, userid, password):
        service_name = "kayttooikeus-service"
        try:
            omattiedot_url = settings.OPINTOPOLKU_DOMAIN + "/" + service_name + '/henkilo/current/omattiedot'
            r = requests.get(omattiedot_url, headers=get_authentication_header(service_name, userid, password))
        except requests.exceptions.RequestException as e:
            logger.error(e)
            msg = _('Connection problems. Please try again later.')
            raise exceptions.AuthenticationFailed(msg)

        if r.status_code == 200:  # user was authenticated successfully from cas
            pass
        elif r.status_code == 401:
            msg = _('Authentication failed.')
            raise exceptions.AuthenticationFailed(msg)
        else:
            logger.error('User authentication failed with status_code: ' + str(r.status_code))
            msg = _('Authentication failed.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            omattiedot = json.loads(r.content)
        except json.JSONDecodeError:
            logger.error('Cas-authentication failed. Invalid json.')
            msg = _('An internal error occured. Team is investigating.')
            raise exceptions.AuthenticationFailed(msg)

        # Check we have all the necessary keys in the json
        required_keys = set(('kayttajaTyyppi', 'username', 'oidHenkilo', 'organisaatiot'))
        if set(omattiedot) >= required_keys:
            pass  # Correct. We have all info.
        else:
            logger.error('Cas-authentication failed. Missing parameters in json.')
            msg = _('An internal error occured. Team is investigating.')
            raise exceptions.AuthenticationFailed(msg)

        cas_henkilo_kayttajaTyyppi = omattiedot["kayttajaTyyppi"]
        if cas_henkilo_kayttajaTyyppi != "PALVELU":
            msg = _('Did not find an active palvelukayttaja-profile.')
            raise exceptions.AuthenticationFailed(msg)

        return omattiedot

    def authenticate_credentials(self, userid, password, request=None):
        """
        Basic authentication, in the first place, is only allowed for fetching the apikey-token.
        Never in any other situation.
        """
        if request is not None:
            path = request.get_full_path()
            if path == "/api/user/apikey/":
                pass
            else:
                msg = _('Basic authentication not allowed.')
                raise exceptions.AuthenticationFailed(msg)

        """
        Authenticate user via CAS, and get "omattiedot" for the user.
        """
        omattiedot = self.authenticate_and_get_omattiedot(userid, password)
        cas_henkilo_kayttajaTyyppi = omattiedot["kayttajaTyyppi"]

        cas_username = omattiedot["username"]
        cas_henkilo_oid = omattiedot["oidHenkilo"]
        cas_henkilo_organisaatiot = omattiedot["organisaatiot"]

        # Do we have the user in our DB. If not, create it.
        try:
            user = User.objects.get(username=cas_username)
        except User.DoesNotExist:
            user = User.objects.create_user(username=cas_username, password=uuid.uuid4().hex)
            user.set_unusable_password()  # Because the user is authenticated via cas, we need to set the varda-password unusable
        except User.MultipleObjectsReturned:  # This should never be possible
            logger.error('Multiple of user-instances found.')
            msg = _('An internal error occured. Team is investigating.')
            raise exceptions.AuthenticationFailed(msg)

        if user is None:
            raise exceptions.AuthenticationFailed(_('Invalid username/password.'))

        if not user.is_active:
            raise exceptions.AuthenticationFailed(_('User inactive or deleted.'))

        """
        Should we ratelimit the user. We do not want to let the users call this api-endpoint too frequently.
        There should be no use case to fetch the token more frequently than ~once a day.
        """
        self.ratelimit_basic_auth_user(user)

        """
        Add/Update miscellaneous user-fields
        """
        obj, created = Z3_AdditionalCasUserFields.objects.update_or_create(user=user, defaults={'kayttajatyyppi': cas_henkilo_kayttajaTyyppi, 'henkilo_oid': cas_henkilo_oid})

        """
        We need to delete the "kayttooikeus" groups first (there might be removed access rights).
        After removal, let's update the access rights.
        """
        Z4_CasKayttoOikeudet.objects.filter(user=user).delete()
        self.update_permission_groups(user, cas_henkilo_organisaatiot)

        return (user, None)

    def ratelimit_basic_auth_user(self, user):
        try:
            user_details_obj = Z3_AdditionalCasUserFields.objects.get(user=user)
        except Z3_AdditionalCasUserFields.DoesNotExist:
            user_details_obj = None

        if user_details_obj is not None:
            user_details_last_modified = user_details_obj.last_modified
            time_now = datetime.now(timezone.utc)
            time_difference_in_seconds = (time_now - user_details_last_modified) / timedelta(seconds=1)
            if time_difference_in_seconds < settings.BASIC_AUTHENTICATION_LOGIN_INTERVAL_IN_SECONDS:
                available_in_seconds = int(settings.BASIC_AUTHENTICATION_LOGIN_INTERVAL_IN_SECONDS - time_difference_in_seconds)
                raise exceptions.Throttled(wait=available_in_seconds)

    def update_permission_groups(self, user, cas_henkilo_organisaatiot):
        list_of_organizations_user_has_permissions = []  # PALVELUKAYTTAJA should have permissions only to one organization.

        for organisaatio in cas_henkilo_organisaatiot:
            # For PALVELUKAYTTAJA, Varda is only interested about permissions on vaka-jarjestaja organization-level.
            if organization_is_not_active_vaka_organization(organisaatio["organisaatioOid"], must_be_vakajarjestaja=True):
                continue

            for kayttooikeus in organisaatio["kayttooikeudet"]:
                if kayttooikeus["palvelu"] == "VARDA" and kayttooikeus["oikeus"] == Z4_CasKayttoOikeudet.PALVELUKAYTTAJA:
                    list_of_organizations_user_has_permissions.append((organisaatio["organisaatioOid"], kayttooikeus["oikeus"]))  # add tuple to list

        if len(list_of_organizations_user_has_permissions) == 1:
            organisaatio_tuple = list_of_organizations_user_has_permissions[0]
            organisaatio_oid = organisaatio_tuple[0]
            kayttooikeus = organisaatio_tuple[1]
            k, created = Z4_CasKayttoOikeudet.objects.get_or_create(user=user, organisaatio_oid=organisaatio_oid, defaults={"kayttooikeus": kayttooikeus})
            if not created:
                logger.info("Already had kayttooikeudet for user: " + user.username + ", organisaatio_oid: " + organisaatio_oid)

            vakajarjestaja = VakaJarjestaja.objects.filter(organisaatio_oid=organisaatio_oid)
            if vakajarjestaja.exists():  # There is only one vakajarjestaja, organisaatio_oid is unique
                vakajarjestaja_obj = vakajarjestaja[0]
                if not vakajarjestaja_obj.integraatio_organisaatio:
                    vakajarjestaja_obj.integraatio_organisaatio = True
                    vakajarjestaja_obj.save()

            else:
                # VakaJarjestaja doesn't exist yet, let's create it.
                create_vakajarjestaja_using_oid(organisaatio_oid, user.id, integraatio_organisaatio=True)

            user.groups.clear()  # First remove the permission_groups from user
            organization_specific_permission_group = get_permission_group(kayttooikeus, organisaatio_oid)
            if organization_specific_permission_group is not None:
                organization_specific_permission_group.user_set.add(user)  # Assign the user to this permission_group

            """
            Finally, add palvelukayttaja to the "vakajarjestaja_view_henkilo" group
            """
            group = Group.objects.get(name="vakajarjestaja_view_henkilo")
            group.user_set.add(user)

        else:
            """
            Decline the access to Varda if the "palvelukayttaja" doesn't have correct
            permissions to VARDA-service in one active vaka-organization.
            """
            msg = _('Palvelukayttaja does not have Varda-permissions to just one active vaka-organization.')
            raise exceptions.AuthenticationFailed(msg)
