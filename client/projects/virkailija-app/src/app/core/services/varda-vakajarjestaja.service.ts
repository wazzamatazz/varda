import {Injectable} from '@angular/core';
import {VardaToimipaikkaDTO, VardaVakajarjestaja, VardaVakajarjestajaUi, VardaVarhaiskasvatussuhdeDTO} from '../../utilities/models';
import {BehaviorSubject, Observable, Subject} from 'rxjs';
import {AuthService} from '../auth/auth.service';
import {VardaToimipaikkaMinimalDto} from '../../utilities/models/dto/varda-toimipaikka-dto.model';
import {deprecate} from 'util';

@Injectable()
export class VardaVakajarjestajaService {

  vakaJarjestajat: Array<VardaVakajarjestajaUi>;
  vakaJarjestajatSubject = new Subject<Array<VardaVakajarjestajaUi>>();
  selectedVakajarjestaja: VardaVakajarjestajaUi;
  selectedVakajarjestajaSubject = new BehaviorSubject<any>({});
  selectedToimipaikka: VardaToimipaikkaMinimalDto;
  selectedToimipaikkaSubject = new Subject<VardaToimipaikkaMinimalDto>();
  tallentajaToimipaikat: Array<VardaToimipaikkaMinimalDto>;
  toimipaikat: Array<VardaToimipaikkaDTO>;
  tallentajaToimipaikatSubject = new Subject<Array<VardaToimipaikkaDTO>>();
  toimipaikkaVarhaiskasvatussuhteet: Array<VardaVarhaiskasvatussuhdeDTO>;
  private selectedToimipaikkaOid = new BehaviorSubject<string>(null);

  constructor() { }

  getVakajarjestajat(): Array<VardaVakajarjestajaUi> {
    return this.vakaJarjestajat;
  }

  setVakajarjestajat(vardaVakaJarjestajat: Array<VardaVakajarjestajaUi>): void {
    this.vakaJarjestajat = vardaVakaJarjestajat;
    this.setVakajarjestajatSubject(vardaVakaJarjestajat);
  }

  setVakajarjestajatSubject(vardaVakaJarjestajat: Array<VardaVakajarjestajaUi>) {
    this.vakaJarjestajatSubject.next(vardaVakaJarjestajat);
  }

  getVakajarjestajatObs(): Observable<Array<VardaVakajarjestajaUi>> {
    return this.vakaJarjestajatSubject.asObservable();
  }

  setSelectedVakajarjestaja(vakajarjestaja: VardaVakajarjestajaUi, onVakajarjestajaChange?: boolean): void {
    this.selectedVakajarjestaja = vakajarjestaja;
    localStorage.setItem('varda.selectedvakajarjestaja', JSON.stringify(vakajarjestaja));
    this.setSelectedVakajarjestajaSubject(vakajarjestaja, onVakajarjestajaChange);
  }

  getSelectedVakajarjestaja(): VardaVakajarjestajaUi {
    return this.selectedVakajarjestaja;
  }

  getSelectedVakajarjestajaId(): string {
    return this.getSelectedVakajarjestaja().id;
  }

  getSelectedToimipaikka(): VardaToimipaikkaMinimalDto {
    return this.selectedToimipaikka;
  }

  setSelectedToimipaikka(toimipaikka: VardaToimipaikkaMinimalDto) {
    this.selectedToimipaikka = toimipaikka;
  }

  setSelectedToimipaikkaSubject(toimipaikka: VardaToimipaikkaMinimalDto) {
    this.selectedToimipaikkaSubject.next(toimipaikka);
  }

  getSelectedToimipaikkaObs(): Observable<VardaToimipaikkaMinimalDto> {
    return this.selectedToimipaikkaSubject.asObservable();
  }

  setSelectedVakajarjestajaSubject(vakajarjestaja: VardaVakajarjestajaUi, onVakajarjestajaChange?: boolean) {
    this.selectedVakajarjestajaSubject.next({vakajarjestaja: vakajarjestaja, onVakajarjestajaChange: onVakajarjestajaChange});
  }

  getSelectedVakajarjestajaObs(): Observable<any> {
    return this.selectedVakajarjestajaSubject.asObservable();
  }

  getToimipaikat():  Array<VardaToimipaikkaDTO> {
    return this.toimipaikat;
  }

  setToimipaikat(toimipaikat: Array<VardaToimipaikkaMinimalDto>, authService?: AuthService): void {
    this.toimipaikat = toimipaikat;
    if (authService) {
      this.setTallentajaToimipaikat(toimipaikat, authService);
    }
  }

  /**
   * @deprecated Not working properly. Essentially returns all toimipaikat.
   */
  getTallentajaToimipaikat(): Array<VardaToimipaikkaMinimalDto> {
    return this.tallentajaToimipaikat;
  }

  /**
   * @deprecated Underlying function not working properly. Values are not what's expected.
   */
  setTallentajaToimipaikat(toimipaikat: Array<VardaToimipaikkaMinimalDto>, authService: AuthService): void {
    this.tallentajaToimipaikat = authService.getAuthorizedToimipaikat(toimipaikat);
    this.setTallentajaToimipaikatSubject(toimipaikat);
  }

  setTallentajaToimipaikatSubject(toimipaikat: Array<VardaToimipaikkaDTO>) {
    this.tallentajaToimipaikatSubject.next(toimipaikat);
  }

  getTallentajaToimipaikatObs(): Observable<Array<VardaToimipaikkaDTO>> {
    return this.tallentajaToimipaikatSubject.asObservable();
  }

  getVarhaiskasvatussuhteet(): Array<VardaVarhaiskasvatussuhdeDTO> {
    return this.toimipaikkaVarhaiskasvatussuhteet;
  }

  setVarhaiskasvatussuhteet(varhaiskasvatussuhteet: Array<VardaVarhaiskasvatussuhdeDTO>): void {
    this.toimipaikkaVarhaiskasvatussuhteet = varhaiskasvatussuhteet;
  }

  getVakajarjestajaByUrl(url: string, vakajarjestajat: Array<VardaVakajarjestaja>): VardaVakajarjestaja {
    return vakajarjestajat.find((t) => t.url === url);
  }

  setSelectedToimipaikkaOid(toimipaikka_oid: string) {
    this.selectedToimipaikkaOid.next(toimipaikka_oid);
  }

  getSelectedToimipaikkaOid() {
    return this.selectedToimipaikkaOid;
  }
}
