import {forkJoin, of as observableOf} from 'rxjs';
import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';
import {VardaFieldSet, VardaKayttooikeusRoles, VardaToimipaikkaDTO} from '../../../utilities/models';
import {VardaApiService} from '../../../core/services/varda-api.service';
import {VardaLocalstorageWrapperService} from '../../../core/services/varda-localstorage-wrapper.service';
import {VardaApiWrapperService} from '../../../core/services/varda-api-wrapper.service';
import {VardaVakajarjestajaService} from '../../../core/services/varda-vakajarjestaja.service';
import {VardaModalService} from '../../../core/services/varda-modal.service';
import {VardaUtilityService} from '../../../core/services/varda-utility.service';
import {AuthService} from '../../../core/auth/auth.service';
import {Lahdejarjestelma} from '../../../utilities/models/enums/lahdejarjestelma';
import {VardaFieldsetArrayContainer} from '../../../utilities/models/varda-fieldset.model';
import {ModalEvent} from '../../../shared/components/varda-modal-form/varda-modal-form.component';
import {VardaToimipaikkaMinimalDto} from '../../../utilities/models/dto/varda-toimipaikka-dto.model';

@Component({
  selector: 'app-varda-toimipaikka-selector',
  templateUrl: './varda-toimipaikka-selector.component.html',
  styleUrls: ['./varda-toimipaikka-selector.component.css']
})
export class VardaToimipaikkaSelectorComponent implements OnInit, OnChanges {

  @Input() entityType: string;
  @Input() toimipaikat: Array<VardaToimipaikkaMinimalDto>;
  @Input() activeToimipaikka: VardaToimipaikkaMinimalDto;
  @Output() changeToimipaikka: EventEmitter<any> = new EventEmitter();
  @Output() updateToimipaikka: EventEmitter<boolean> = new EventEmitter();
  @Output() closeToimipaikkaForm: EventEmitter<any> = new EventEmitter();
  @Output() toggleToimipaikkaSelectorVisibility: EventEmitter<any> = new EventEmitter();
  toimipaikkaData: VardaToimipaikkaDTO;

  toimipaikkaFieldSets: Array<VardaFieldSet>;
  toimipaikkaFormOpen: boolean;
  editToimipaikkaAction: boolean;
  isOrganisationLevelTallentajaRole: boolean;
  lahdejarjestelmaTypes = Lahdejarjestelma;

  ui: {
    isLoading: boolean,
    editLabelText: string
  };

  confirmedToimipaikkaFormLeave = true;
  isDisplayingSuccessModal = false;

  constructor(private vardaApiService: VardaApiService,
    private vardaApiWrapperService: VardaApiWrapperService,
    private vardaLocalStorageWrapperService: VardaLocalstorageWrapperService,
    private vardaVakajarjestajaService: VardaVakajarjestajaService,
    private vardaUtilityService: VardaUtilityService,
    private vardaModalService: VardaModalService,
    private authService: AuthService) {
      this.ui = {
        isLoading: false,
        editLabelText: 'label.show-and-edit'
      };
      this.toimipaikkaFormOpen = false;

      this.vardaModalService.modalOpenObs('toimipaikkaSuccessModal').subscribe((isOpen: boolean) => {
        if (isOpen) {
          this.isDisplayingSuccessModal = true;
        }
      });

      this.authService.loggedInUserKayttooikeudetSubject.asObservable().subscribe(() => {
        this.initKayttooikeudet();
        this.ui.isLoading = false;
      });
  }

  initKayttooikeudet(): void {
    this.isOrganisationLevelTallentajaRole =
      this.authService.selectedOrganisationLevelKayttooikeusRole === VardaKayttooikeusRoles.VARDA_TALLENTAJA;
  }

  byEndpoint(item1: any, item2: any): boolean {
    if (!item1 || !item2) {
      return false;
    }
    return item1.url === item2.url;
  }

  initToimipaikat(toimipaikat: Array<VardaToimipaikkaDTO>): void {

    if (this.toimipaikat.length === 0) {
      this.activeToimipaikka = null;
      return;
    }

    if (this.toimipaikat.length === 1) {
      this.activeToimipaikka = this.toimipaikat[0];
      this.vardaVakajarjestajaService.setSelectedToimipaikka(this.activeToimipaikka);
      this.changeToimipaikka.emit(this.activeToimipaikka);
      return;
    }

    this.toimipaikat = this.toimipaikat.sort((a, b) => {
      return a.nimi.toLowerCase().localeCompare(b.nimi.toLowerCase(), 'fi');
    });

    const activeToimipaikkaFromLocalStorage = this.vardaLocalStorageWrapperService.getFromLocalStorage('varda.activeToimipaikka');
    if (activeToimipaikkaFromLocalStorage) {
      const parsedToimipaikka = JSON.parse(activeToimipaikkaFromLocalStorage);
      this.activeToimipaikka = this.getToimipaikkaByUrl(parsedToimipaikka.url, this.toimipaikat);
      this.vardaVakajarjestajaService.setSelectedToimipaikka(this.activeToimipaikka);
      this.vardaVakajarjestajaService.setSelectedToimipaikkaSubject(this.activeToimipaikka);
      this.changeToimipaikka.emit(this.activeToimipaikka);
    }
  }

  updateToimipaikat(data: any): void {
    if (data.toimipaikka) {
      this.activeToimipaikka = data.toimipaikka;
      this.vardaVakajarjestajaService.setSelectedToimipaikka(this.activeToimipaikka);
      this.updateToimipaikka.emit(data.toimipaikka);
    }
  }

  handleFormClose($eventObject: ModalEvent): void {
    if ($eventObject === ModalEvent.hidden) {
      this.toimipaikkaFormOpen = false;
      this.confirmedToimipaikkaFormLeave = true;
    }
  }

  addToimipaikka(): void {
    this.editToimipaikkaAction = false;
    this.openToimipaikkaForm();
  }

  editToimipaikka(): void {
    this.editToimipaikkaAction = true;
    this.openToimipaikkaForm();
  }

  setToimipaikka(): void {
    this.vardaVakajarjestajaService.setSelectedToimipaikkaSubject(this.activeToimipaikka);
    this.vardaVakajarjestajaService.setSelectedToimipaikka(this.activeToimipaikka);
    this.vardaLocalStorageWrapperService.saveToLocalStorage('varda.activeToimipaikka', JSON.stringify(this.activeToimipaikka));
    this.changeToimipaikka.emit(this.activeToimipaikka);
  }

  openToimipaikkaForm(): void {
    this.ui.isLoading = true;

    let obs;
    if (!this.activeToimipaikka) {
      obs = observableOf(null);
    } else {
      const toimipaikkaId = this.vardaUtilityService.parseIdFromUrl(this.activeToimipaikka.url);
      obs = this.vardaApiWrapperService.getToimipaikkaById(toimipaikkaId);
    }

    forkJoin([
      this.vardaApiService.getToimipaikkaFields(),
      obs,
    ]).subscribe((data: [VardaFieldsetArrayContainer, VardaToimipaikkaDTO]) => {
      const toimipaikkadata = data[0];
      this.toimipaikkaFieldSets = toimipaikkadata.fieldsets;
      this.toimipaikkaFormOpen = true;
      this.toimipaikkaData = data[1];
      this.ui.isLoading = false;
    });
  }

  toimipaikkaFormValuesChanged(hasChanged: boolean) {
    this.confirmedToimipaikkaFormLeave = !hasChanged;
  }

  getToimipaikkaByUrl(url: string, toimipaikat: Array<VardaToimipaikkaMinimalDto>): VardaToimipaikkaMinimalDto {
    return toimipaikat.find((t) => t.url === url);
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes.toimipaikat &&
      changes.toimipaikat.currentValue &&
      changes.toimipaikat.currentValue.length > 0) {
        setTimeout(() => {
          this.initToimipaikat(changes.toimipaikat.currentValue);
        });
    }
  }

  ngOnInit() {
    this.initKayttooikeudet();
  }

}
