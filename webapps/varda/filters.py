from varda.models import (VakaJarjestaja, Toimipaikka, ToiminnallinenPainotus, KieliPainotus, Henkilo,
                          Tyontekija, Taydennyskoulutus, Ohjaajasuhde, Lapsi, Huoltaja, Maksutieto, PaosToiminta,
                          PaosOikeus, Varhaiskasvatuspaatos, Varhaiskasvatussuhde, Z2_Koodisto)
from django.db.models import Q
from django_filters import rest_framework as djangofilters


class CustomCharFilter(djangofilters.CharFilter):
    """
    Custom CharFilter which can be used to filter the query with EMPTY string,
    e.g. /api/v1/toimipaikat/?oid_tunniste=EMPTY
    returns all "toimipaikat" where oid_tunniste == ""
    """
    empty_value = 'EMPTY'

    def filter(self, qs, value):
        if value != self.empty_value:
            return super(CustomCharFilter, self).filter(qs, value)

        qs = self.get_method(qs)(**{'%s__%s' % (self.field_name, self.lookup_expr): ""})
        return qs.distinct() if self.distinct else qs


class CharArrayFilter(djangofilters.BaseCSVFilter, djangofilters.CharFilter):
    pass


class KunnallinenKytkinFilter(djangofilters.BooleanFilter):
    def filter(self, qs, value):
        if value is None:
            return qs
        elif value:
            return qs.filter(yritysmuoto__in=VakaJarjestaja.get_kuntatyypit())
        elif not value:
            return qs.filter(~Q(yritysmuoto__in=VakaJarjestaja.get_kuntatyypit()))


class VakaJarjestajaFilter(djangofilters.FilterSet):
    nimi = djangofilters.CharFilter(field_name='nimi', lookup_expr='icontains')
    y_tunnus = djangofilters.CharFilter(field_name='y_tunnus', lookup_expr='exact')
    organisaatio_oid = CustomCharFilter(field_name='organisaatio_oid', lookup_expr='exact')
    kunta_koodi = djangofilters.CharFilter(field_name='kunta_koodi', lookup_expr='exact')
    sahkopostiosoite = CustomCharFilter(field_name='sahkopostiosoite', lookup_expr='exact')
    tilinumero = djangofilters.CharFilter(field_name='tilinumero', lookup_expr='exact')
    ipv4_osoitteet = CharArrayFilter(field_name='ipv4_osoitteet', lookup_expr='contains')
    ipv6_osoitteet = CharArrayFilter(field_name='ipv6_osoitteet', lookup_expr='contains')
    kayntiosoite = djangofilters.CharFilter(field_name='kayntiosoite', lookup_expr='icontains')
    kayntiosoite_postitoimipaikka = djangofilters.CharFilter(field_name='kayntiosoite_postitoimipaikka', lookup_expr='icontains')
    kayntiosoite_postinumero = djangofilters.CharFilter(field_name='kayntiosoite_postinumero', lookup_expr='exact')
    postiosoite = djangofilters.CharFilter(field_name='postiosoite', lookup_expr='icontains')
    postitoimipaikka = djangofilters.CharFilter(field_name='postitoimipaikka', lookup_expr='icontains')
    postinumero = djangofilters.CharFilter(field_name='postinumero', lookup_expr='exact')
    puhelinnumero = CustomCharFilter(field_name='puhelinnumero', lookup_expr='exact')
    ytjkieli = djangofilters.CharFilter(field_name='ytjkieli', lookup_expr='exact')
    kunnallinen_kytkin = KunnallinenKytkinFilter(label='kunnallinen_kytkin')
    alkamis_pvm = djangofilters.DateFilter(field_name='alkamis_pvm', lookup_expr='gte')
    paattymis_pvm = djangofilters.DateFilter(field_name='paattymis_pvm', lookup_expr='gte')
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = VakaJarjestaja
        fields = []


class ToimipaikkaFilter(djangofilters.FilterSet):
    nimi = djangofilters.CharFilter(field_name='nimi', lookup_expr='icontains')
    organisaatio_oid = CustomCharFilter(field_name='organisaatio_oid', lookup_expr='exact')
    kayntiosoite = djangofilters.CharFilter(field_name='kayntiosoite', lookup_expr='icontains')
    kayntiosoite_postitoimipaikka = djangofilters.CharFilter(field_name='kayntiosoite_postitoimipaikka', lookup_expr='icontains')
    kayntiosoite_postinumero = djangofilters.CharFilter(field_name='kayntiosoite_postinumero', lookup_expr='exact')
    postiosoite = djangofilters.CharFilter(field_name='postiosoite', lookup_expr='icontains')
    postitoimipaikka = djangofilters.CharFilter(field_name='postitoimipaikka', lookup_expr='icontains')
    postinumero = djangofilters.CharFilter(field_name='postinumero', lookup_expr='exact')
    puhelinnumero = CustomCharFilter(field_name='puhelinnumero', lookup_expr='exact')
    sahkopostiosoite = CustomCharFilter(field_name='sahkopostiosoite', lookup_expr='exact')
    kasvatusopillinen_jarjestelma_koodi = CustomCharFilter(field_name='kasvatusopillinen_jarjestelma_koodi', lookup_expr='exact')
    toimintamuoto_koodi = CustomCharFilter(field_name='toimintamuoto_koodi', lookup_expr='exact')
    asiointikieli_koodi = CharArrayFilter(field_name='asiointikieli_koodi', lookup_expr='contains')
    jarjestamismuoto_koodi = CharArrayFilter(field_name='jarjestamismuoto_koodi', lookup_expr='contains')
    varhaiskasvatuspaikat = djangofilters.NumberFilter(field_name='varhaiskasvatuspaikat', lookup_expr='gte')
    alkamis_pvm = djangofilters.DateFilter(field_name='alkamis_pvm', lookup_expr='gte')
    paattymis_pvm = djangofilters.DateFilter(field_name='paattymis_pvm', lookup_expr='gte')
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = Toimipaikka
        fields = []


class ToiminnallinenPainotusFilter(djangofilters.FilterSet):
    toimintapainotus_koodi = djangofilters.CharFilter(field_name='toimintapainotus_koodi', lookup_expr='exact')
    alkamis_pvm = djangofilters.DateFilter(field_name='alkamis_pvm', lookup_expr='gte')
    paattymis_pvm = djangofilters.DateFilter(field_name='paattymis_pvm', lookup_expr='gte')
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = ToiminnallinenPainotus
        fields = []


class KieliPainotusFilter(djangofilters.FilterSet):
    kielipainotus_koodi = djangofilters.CharFilter(field_name='kielipainotus_koodi', lookup_expr='exact')
    alkamis_pvm = djangofilters.DateFilter(field_name='alkamis_pvm', lookup_expr='gte')
    paattymis_pvm = djangofilters.DateFilter(field_name='paattymis_pvm', lookup_expr='gte')
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = KieliPainotus
        fields = []


class HenkiloFilter(djangofilters.FilterSet):
    henkilotunnus = CustomCharFilter(field_name='henkilotunnus', lookup_expr='exact')
    henkilo_oid = CustomCharFilter(field_name='henkilo_oid', lookup_expr='exact')

    class Meta:
        model = Henkilo
        fields = []


class HenkiloNimiFilter(djangofilters.FilterSet):
    etunimet = CustomCharFilter(field_name='etunimet', lookup_expr='icontains')
    sukunimi = CustomCharFilter(field_name='sukunimi', lookup_expr='icontains')

    class Meta:
        model = Henkilo
        fields = []


class LapsiFilter(djangofilters.FilterSet):
    paos_kytkin = djangofilters.BooleanFilter(field_name='paos_kytkin', lookup_expr='exact')
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = Lapsi
        fields = []


class HuoltajaFilter(djangofilters.FilterSet):
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = Huoltaja
        fields = []


class TyontekijaFilter(djangofilters.FilterSet):
    tyosuhde_koodi = djangofilters.CharFilter(field_name='tyosuhde_koodi', lookup_expr='exact')
    tyoaika_koodi = djangofilters.CharFilter(field_name='tyoaika_koodi', lookup_expr='exact')
    tutkintonimike_koodi = CharArrayFilter(field_name='tutkintonimike_koodi', lookup_expr='contains')
    alkamis_pvm = djangofilters.DateFilter(field_name='alkamis_pvm', lookup_expr='gte')
    paattymis_pvm = djangofilters.DateFilter(field_name='paattymis_pvm', lookup_expr='gte')
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = Tyontekija
        fields = []


class TaydennyskoulutusFilter(djangofilters.FilterSet):
    tuntimaara = djangofilters.NumberFilter(field_name='tuntimaara', lookup_expr='gte')
    suoritus_pvm = djangofilters.DateTimeFilter(field_name='suoritus_pvm', lookup_expr='gte')
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = Taydennyskoulutus
        fields = []


class OhjaajasuhdeFilter(djangofilters.FilterSet):
    tyotehtava_koodi = djangofilters.CharFilter(field_name='tyotehtava_koodi', lookup_expr='exact')
    tyoaika_viikossa = djangofilters.NumberFilter(field_name='tyoaika_viikossa', lookup_expr='gte')
    alkamis_pvm = djangofilters.DateFilter(field_name='alkamis_pvm', lookup_expr='gte')
    paattymis_pvm = djangofilters.DateFilter(field_name='paattymis_pvm', lookup_expr='gte')
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = Ohjaajasuhde
        fields = []


class MaksutietoFilter(djangofilters.FilterSet):
    maksun_peruste_koodi = djangofilters.CharFilter(field_name='maksun_peruste_koodi', lookup_expr='exact')
    alkamis_pvm = djangofilters.DateFilter(field_name='alkamis_pvm', lookup_expr='gte')
    paattymis_pvm = djangofilters.DateFilter(field_name='paattymis_pvm', lookup_expr='gte')

    class Meta:
        model = Maksutieto
        fields = []


class PaosToimintaFilter(djangofilters.FilterSet):
    oma_organisaatio = djangofilters.NumberFilter(field_name='oma_organisaatio', lookup_expr='exact')
    paos_organisaatio = djangofilters.NumberFilter(field_name='paos_organisaatio', lookup_expr='exact')
    paos_toimipaikka = djangofilters.NumberFilter(field_name='paos_toimipaikka', lookup_expr='exact')

    class Meta:
        model = PaosToiminta
        fields = []


class PaosOikeusFilter(djangofilters.FilterSet):
    jarjestaja_kunta_organisaatio = djangofilters.NumberFilter(field_name='jarjestaja_kunta_organisaatio', lookup_expr='exact')
    tuottaja_organisaatio = djangofilters.NumberFilter(field_name='tuottaja_organisaatio', lookup_expr='exact')

    class Meta:
        model = PaosOikeus
        fields = []


class VarhaiskasvatuspaatosFilter(djangofilters.FilterSet):
    vuorohoito_kytkin = djangofilters.BooleanFilter(field_name='vuorohoito_kytkin', lookup_expr='exact')
    pikakasittely_kytkin = djangofilters.BooleanFilter(field_name='pikakasittely_kytkin', lookup_expr='exact')
    tuntimaara_viikossa = djangofilters.NumberFilter(field_name='tuntimaara_viikossa', lookup_expr='gte')
    paivittainen_vaka_kytkin = djangofilters.BooleanFilter(field_name='paivittainen_vaka_kytkin', lookup_expr='exact')
    kokopaivainen_vaka_kytkin = djangofilters.BooleanFilter(field_name='kokopaivainen_vaka_kytkin', lookup_expr='exact')
    jarjestamismuoto_koodi = djangofilters.CharFilter(field_name='jarjestamismuoto_koodi', lookup_expr='exact')
    hakemus_pvm = djangofilters.DateFilter(field_name='hakemus_pvm', lookup_expr='gte')
    alkamis_pvm = djangofilters.DateFilter(field_name='alkamis_pvm', lookup_expr='gte')
    paattymis_pvm = djangofilters.DateFilter(field_name='paattymis_pvm', lookup_expr='gte')
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = Varhaiskasvatuspaatos
        fields = []


class VarhaiskasvatussuhdeFilter(djangofilters.FilterSet):
    alkamis_pvm = djangofilters.DateFilter(field_name='alkamis_pvm', lookup_expr='gte')
    paattymis_pvm = djangofilters.DateFilter(field_name='paattymis_pvm', lookup_expr='gte')
    muutos_pvm = djangofilters.DateTimeFilter(field_name='muutos_pvm', lookup_expr='gte')

    class Meta:
        model = Varhaiskasvatussuhde
        fields = []


class Z2_Koodisto(djangofilters.FilterSet):
    kunta_koodit = CharArrayFilter(field_name='kunta_koodit', lookup_expr='exact')
    kieli_koodit = CharArrayFilter(field_name='kieli_koodit', lookup_expr='exact')
    jarjestamismuoto_koodit = CharArrayFilter(field_name='jarjestamismuoto_koodis', lookup_expr='exact')
    toimintamuoto_koodit = CharArrayFilter(field_name='toimintamuoto_koodit', lookup_expr='exact')
    kasvatusopillinen_jarjestelma_koodit = CharArrayFilter(field_name='kasvatusopillimem_jarjestelma_koodi', lookup_expr='exact')
    toiminnallinen_painotus_koodit = CharArrayFilter(field_name='toiminnallinen_painotus_koodit', lookup_expr='exact')
    tutkintonimike_koodit = CharArrayFilter(field_name='tutkintonimike_koodit', lookup_expr='exact')
    tyosuhde_koodit = CharArrayFilter(field_name='tyosuhde_koodit', lookup_expr='exact')
    tyoaika_koodit = CharArrayFilter(field_name='tyoaika_koodit', lookup_expr='exact')
    tyotehtava_koodit = CharArrayFilter(field_name='tyotehtava_koodit', lookup_expr='exact')
    sukupuoli_koodit = CharArrayFilter(field_name='sukupuoli_koodit', lookup_expr='exact')
    opiskeluoikeuden_tila_koodit = CharArrayFilter(field_name='opiskeluoikeuden_tila_koodit', lookup_expr='exact')
    tutkinto_koodit = CharArrayFilter(field_name='tutkinto_koodit', lookup_expr='exact')

    class Meta:
        model = Z2_Koodisto
        fields = []
