import {Component, Input, OnChanges, OnInit, SimpleChange, SimpleChanges} from '@angular/core';
import {HenkilohakuResultDTO} from '../../../../utilities/models/dto/varda-henkilohaku-dto.model';
import {TranslateService} from '@ngx-translate/core';
import {VardaHenkiloDTO} from '../../../../utilities/models/dto/varda-henkilo-dto.model';
import {ModalEvent} from '../../../../shared/components/varda-modal-form/varda-modal-form.component';
import {AuthService} from '../../../../core/auth/auth.service';
import {VardaVakajarjestajaService} from '../../../../core/services/varda-vakajarjestaja.service';
import {VardaKayttooikeusRoles} from '../../../../utilities/varda-kayttooikeus-roles';

class HenkiloHakuResultWithToimipaikka {
  lapsi: HenkilohakuResultDTO;
  toimipaikkaName: string;
  toimipaikka_oid: string;
}

@Component({
  selector: 'app-haku-list',
  templateUrl: './haku-list.component.html',
  styleUrls: ['./haku-list.component.css']
})
export class HakuListComponent implements OnInit, OnChanges {
  @Input() searchResult: Array<HenkilohakuResultDTO>;

  searchResultByToimipaikka: Array<HenkiloHakuResultWithToimipaikka>;
  henkiloFormOpen: boolean;
  activeHenkilo: VardaHenkiloDTO;

  userRole: VardaKayttooikeusRoles;
  closeHakuListFormWithoutConfirm: boolean;

  constructor(private translateService: TranslateService,
              private authService: AuthService,
              private vardaVakajarjestajaService: VardaVakajarjestajaService) {
    this.searchResult = [];
    this.henkiloFormOpen = false;
    this.closeHakuListFormWithoutConfirm = true;
  }

  ngOnInit() {
    this.searchResultByToimipaikka = [];
    this.userRole = this.authService.loggedInUserCurrentKayttooikeus;
  }

  ngOnChanges(changes: SimpleChanges): void {
    const searchResult: SimpleChange = changes.searchResult;
    if (searchResult) {
      this.searchResultByToimipaikka = this.flatmapSearchResults(searchResult.currentValue);
    }
  }

  getMaksutietoText(maksutiedot: Array<string>) {
    return maksutiedot.length
      ? 'label.haku-list.maksutieto-found'
      : '';
  }

  flatmapSearchResults(searchResult: Array<HenkilohakuResultDTO>): Array<HenkiloHakuResultWithToimipaikka> {
    const flatMap = (mapFunc, array) =>
      array.reduce((acc, value) =>
        acc.concat(mapFunc(value)), []);
    return flatMap((result: HenkilohakuResultDTO) =>
      [...result.toimipaikat].map(toimipaikka => ({
        toimipaikkaName: this.getToimipaikkaNimiByLang(toimipaikka),
        toimipaikka_oid: toimipaikka.organisaatio_oid,
        lapsi: {...result},
      })), searchResult);
  }

  getToimipaikkaNimiByLang(toimipaikka) {
    return this.translateService.currentLang === 'sv'
      ? toimipaikka.nimi_sv || toimipaikka.nimi
      : toimipaikka.nimi || toimipaikka.nimi_sv;
  }

  hideHenkiloForm($event: ModalEvent) {
    if ($event === ModalEvent.hidden) {
      this.henkiloFormOpen = false;
      this.closeHakuListFormWithoutConfirm = true;
    }
  }

  editHenkilo(result: HenkiloHakuResultWithToimipaikka) {
    this.vardaVakajarjestajaService.setSelectedToimipaikkaOid(result.toimipaikka_oid);
    this.henkiloFormOpen = true;
    const activeHenkilo = new VardaHenkiloDTO();
    const lapsi = result.lapsi;
    activeHenkilo.id = lapsi.id;
    activeHenkilo.henkilo_oid = lapsi.henkilo.henkilo_oid;
    activeHenkilo.syntyma_pvm = lapsi.henkilo.syntyma_pvm;
    activeHenkilo.url = lapsi.url;
    activeHenkilo.etunimet =  lapsi.henkilo.etunimet;
    activeHenkilo.sukunimi = lapsi.henkilo.sukunimi;
    activeHenkilo.lapsi = lapsi.henkilo.lapsi;
    activeHenkilo.tyontekija = lapsi.henkilo.tyontekija;
    this.activeHenkilo = activeHenkilo;
  }

  henkiloHakuFormValuesChanged(hasChanged: boolean) {
    this.closeHakuListFormWithoutConfirm = !hasChanged;
  }
}
