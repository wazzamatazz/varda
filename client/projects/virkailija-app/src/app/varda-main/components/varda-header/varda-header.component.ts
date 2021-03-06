import {AfterViewInit, ChangeDetectorRef, Component, Input, OnInit} from '@angular/core';
import {AuthService} from '../../../core/auth/auth.service';
import {NavigationEnd, Router} from '@angular/router';
import {VardaVakajarjestajaService} from '../../../core/services/varda-vakajarjestaja.service';
import {VardaKayttooikeusRoles, VardaVakajarjestajaUi} from '../../../utilities/models';
import {environment} from '../../../../environments/environment';
import {VardaUtilityService} from '../../../core/services/varda-utility.service';
import {LoginService} from 'varda-shared';

declare var $: any;

@Component({
  selector: 'app-varda-header',
  templateUrl: './varda-header.component.html',
  styleUrls: ['./varda-header.component.css']
})
export class VardaHeaderComponent implements OnInit, AfterViewInit {

  @Input() isDashboardPage: boolean;
  menuOpenState: boolean;
  toimipaikkaSelected: boolean;
  loggedInUserUsername: string;
  selectedVakajarjestaja: VardaVakajarjestajaUi;
  vakajarjestajat: Array<VardaVakajarjestajaUi>;
  activeNavItem: string;

  $siteTitle;
  $siteMenuWrapper;
  $toimipaikkaPanelSelectorHeader;

  isKatselija: boolean;
  canViewToimijanTiedot: boolean;

  ui: {
    isLoading: boolean;
  };
  toimijanTiedotRouteMaps = [];

  constructor(
    private authService: AuthService,
    private loginService: LoginService,
    private router: Router,
    private vardaVakajarjestajaService: VardaVakajarjestajaService,
    private ref: ChangeDetectorRef,
    private vardaUtilityService: VardaUtilityService) {
      this.ui = {isLoading: false};
      this.router.events.subscribe((s) => {

        let activeNavItemStr = '';
        if (s instanceof NavigationEnd) {
          const url = s.url;
          const urlParts = url.split('/');

          if (url === '/') {
            activeNavItemStr = 'toimipaikatjalapset';
          } else if (url === '/vakatoimija') {
            activeNavItemStr = 'vakatoimija';
          } else if (url === '/haku') {
            activeNavItemStr = 'haku';
          } else if (url === '/tietojen-katselu') {
            activeNavItemStr = 'tietojen-katselu';
          } else if (url === '/ohjeet') {
            activeNavItemStr = 'ohjeet';
          }

          if (urlParts && urlParts[1] === 'ohjeet' && urlParts.length === 3) {
            activeNavItemStr = 'ohjeet';
          }

          this.setActiveNavItem(activeNavItemStr);
        }
      });

      this.vardaVakajarjestajaService.getSelectedVakajarjestajaObs().subscribe((data) => {
        this.selectedVakajarjestaja = data.vakajarjestaja;
      });

      this.vardaVakajarjestajaService.getVakajarjestajatObs().subscribe(() => {
        this.vakajarjestajat = this.vardaVakajarjestajaService.getVakajarjestajat();
        try {
          this.vakajarjestajat.sort(this.sortVakajarjestajatByNimi);
        } catch (e) {
          console.log('Error on vakajarjestajat sorting', e);
        }
      });

      this.authService.loggedInUserKayttooikeudetSubject.asObservable().subscribe(() => {
        this.initKayttooikeudet();
        this.ui.isLoading = false;
      });
  }

  changeVakajarjestaja(): void {
    this.vardaVakajarjestajaService.setSelectedVakajarjestaja(this.selectedVakajarjestaja, true);
  }

  initKayttooikeudet(): void {
    const kayttooikeusToEvaluate = this.authService.loggedInUserCurrentKayttooikeus;
    this.isKatselija = kayttooikeusToEvaluate !== VardaKayttooikeusRoles.VARDA_TALLENTAJA;
    // All users are allowed to view these pages
    const vakatoimijaRoute = {
      route: '/vakatoimija',
      textKey: 'label.yhteystiedot',
      isHidden: false,
    };
    const paosRoute = {
      route: '/paos-hallinta',
      textKey: 'label.paostoiminta',
      isHidden: false,
    };
    this.toimijanTiedotRouteMaps = [vakatoimijaRoute, paosRoute];
    this.canViewToimijanTiedot = true;
  }

  isAuthenticated(): boolean {
    return this.loginService.validApiToken;
  }

  logout(): void {
    this.loginService.logout(environment.vardaAppUrl, 'varda');
    this.router.navigate(['/login'], {skipLocationChange: true});
  }

  moveToToimipaikkaSelector(e: any): void {
    if (e.keyCode === 9 && this.$siteMenuWrapper.is(':focus') && !e.shiftKey) {
      setTimeout(() => {
        this.$toimipaikkaPanelSelectorHeader.focus();
      });
    }
  }

  onMenuClosed($event: any): void {
    this.menuOpenState = false;
    this.$siteMenuWrapper.focus();
    this.ref.detectChanges();
  }

  sortVakajarjestajatByNimi(a: any, b: any): number {
    const aNimi = a.nimi.toUpperCase();
    const bNimi = b.nimi.toUpperCase();

    if (aNimi < bNimi) {
      return -1;
    }

    if (aNimi > bNimi) {
      return 1;
    }

    return 0;
  }

  ngAfterViewInit() {
    this.vardaVakajarjestajaService.getSelectedToimipaikkaObs().subscribe((toimipaikka) => {
      setTimeout(() => {
        this.toimipaikkaSelected = toimipaikka ? true : false;
      });
    });
    setTimeout(() => {
      try {
        this.loggedInUserUsername = this.loginService.getUsername();
      } catch (e) {}
    }, 3000);

    this.$siteTitle = $('#siteTitle');
    this.$siteMenuWrapper = $('#siteMenuWrapper');

    setTimeout(() => {
      this.$toimipaikkaPanelSelectorHeader = $('#toimipaikkaSelectorPanel mat-expansion-panel-header');
    }, 2000);

    this.$siteTitle.focus();

    $(document).keydown(this.moveToToimipaikkaSelector.bind(this));
  }

  reloadPage(): void {
    window.location.reload();
  }

  setActiveNavItem(activeNavItemStr: string): void {
    this.activeNavItem = activeNavItemStr;
  }

  ngOnInit() {
    this.ui.isLoading = true;
    if (environment.production) {
      const virkailijaRaamitUrl = this.vardaUtilityService.getVirkailijaRaamitUrl(window.location.hostname);
      if (virkailijaRaamitUrl) {
        const node = document.createElement('script');
        node.src = virkailijaRaamitUrl;
        node.type = 'text/javascript';
        node.async = true;
        node.charset = 'utf-8';
        document.getElementsByTagName('head')[0].appendChild(node);
      }
    }
  }

}
