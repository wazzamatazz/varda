import { Component, OnInit } from '@angular/core';
import { VardaApiWrapperService } from '../../../core/services/varda-api-wrapper.service';
import { VardaVakajarjestajaService } from '../../../core/services/varda-vakajarjestaja.service';
import { VardaUtilityService } from '../../../core/services/varda-utility.service';
import {VardaToimipaikkaDTO, VardaExtendedHenkiloModel, VardaHenkiloDTO, VardaLapsiDTO} from '../../../utilities/models';
import { of } from 'rxjs';
import {AuthService} from '../../../core/auth/auth.service';
import {LapsiByToimipaikkaDTO} from '../../../utilities/models/dto/varda-henkilohaku-dto.model';
import {VardaToimipaikkaMinimalDto} from '../../../utilities/models/dto/varda-toimipaikka-dto.model';

@Component({
  selector: 'app-varda-main-frame',
  templateUrl: './varda-main-frame.component.html',
  styleUrls: ['./varda-main-frame.component.css']
})
export class VardaMainFrameComponent implements OnInit {

  selectedToimipaikka: VardaToimipaikkaMinimalDto;
  toimipaikat: Array<VardaToimipaikkaMinimalDto>;
  henkilot: Array<VardaExtendedHenkiloModel>;

  ui: {
    isFetchingVarhaiskasvatussuhteet: boolean
  };

  constructor(
    private vardaApiWrapperService: VardaApiWrapperService,
    private vardaVakajarjestajaService: VardaVakajarjestajaService,
    private authService: AuthService,
    private vardaUtilityService: VardaUtilityService) {
    this.ui = {
      isFetchingVarhaiskasvatussuhteet: false
    };
    this.vardaVakajarjestajaService.getTallentajaToimipaikatObs().subscribe(() => {
      this.initToimipaikat();
    });
  }

  onToimipaikkaChanged(data: any): void {
    if (!data) {
      return;
    }

    this.selectedToimipaikka = this.vardaVakajarjestajaService.getSelectedToimipaikka();
    this.getVarhaiskasvatussuhteetByToimipaikka();
  }

  onToimipaikkaUpdated(data: any): void {
    const toimipaikkaIndexToUpdate = this.toimipaikat.findIndex((toimipaikkaObj) => toimipaikkaObj.url === data.url);
    let isNew = false;
    if (this.toimipaikat[toimipaikkaIndexToUpdate]) {
      this.toimipaikat[toimipaikkaIndexToUpdate] = data;
    } else {
      isNew = true;
      this.toimipaikat.push(data);
    }

    this.selectedToimipaikka = this.vardaVakajarjestajaService.getSelectedToimipaikka();
    this.vardaVakajarjestajaService.setToimipaikat(this.toimipaikat, this.authService);

    if (isNew) {
      this.getVarhaiskasvatussuhteetByToimipaikka();
    }
  }

  getVarhaiskasvatussuhteetByToimipaikka(): void {
    this.ui.isFetchingVarhaiskasvatussuhteet = true;
    if (!this.vardaVakajarjestajaService.getSelectedToimipaikka()) {
      this.ui.isFetchingVarhaiskasvatussuhteet = false;
      return;
    }
    const selectedTomipaikka = this.vardaVakajarjestajaService.getSelectedToimipaikka();
    if (!selectedTomipaikka) {
      throw Error('No toimipaikka selected. Unable to fetch lapset for toimipaikka.');
    }
    const toimipaikkaId = this.vardaUtilityService.parseIdFromUrl(selectedTomipaikka.url);
    this.vardaApiWrapperService.getAllLapsetForToimipaikka(toimipaikkaId)
    .subscribe({
      next: (lapset: Array<LapsiByToimipaikkaDTO>) => {
        // Filter duplicates since /toimipaikka/#/lapset api returns actually vakasuhde, not henkilo
        this.henkilot = lapset.filter((lapsi, index, self) => index === self.findIndex((otherLapsi) => (
          otherLapsi.henkilo_oid === lapsi.henkilo_oid && otherLapsi.lapsi_id === lapsi.lapsi_id
        ))).map(lapsi => {
          const henkiloExtendedDto = new VardaExtendedHenkiloModel();
          const henkiloDto = new VardaHenkiloDTO();
          henkiloDto.etunimet = lapsi.etunimet;
          henkiloDto.sukunimi = lapsi.sukunimi;
          henkiloDto.henkilo_oid = lapsi.henkilo_oid;
          henkiloDto.syntyma_pvm = lapsi.syntyma_pvm;
          henkiloDto.lapsi = [lapsi.lapsi_url];
          henkiloDto.url = lapsi.lapsi_url;
          henkiloDto.id = lapsi.lapsi_id;
          henkiloExtendedDto.henkilo = henkiloDto;
          henkiloExtendedDto.isNew = false;
          return henkiloExtendedDto;
        });
        this.ui.isFetchingVarhaiskasvatussuhteet = false;
      },
      error: () => this.ui.isFetchingVarhaiskasvatussuhteet = false,
    });
  }

  updateToimipaikatAndVakasuhteet(): void {
    this.ui.isFetchingVarhaiskasvatussuhteet = true;
    of(null).subscribe(() => {
      this.getVarhaiskasvatussuhteetByToimipaikka();
    }, () => {
      this.ui.isFetchingVarhaiskasvatussuhteet = false;
    });
  }

  initToimipaikat(): void {
    this.toimipaikat = this.vardaVakajarjestajaService.getTallentajaToimipaikat();
  }

  ngOnInit() {
    setTimeout(() => {
      this.initToimipaikat();
    });
  }
}
