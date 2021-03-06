import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {Subject} from 'rxjs';

@Component({
  selector: 'app-varda-prompt-modal',
  templateUrl: './varda-prompt-modal.component.html',
  styleUrls: ['./varda-prompt-modal.component.css']
})
export class VardaPromptModalComponent implements OnInit {
  showModal: boolean;
  @Input() show$: Subject<boolean>;
  @Output() saveEvent = new EventEmitter(true);

  constructor() { }

  ngOnInit() {
    this.showModal = false;
    this.show$.subscribe({
      next: isShow => this.showModal = isShow,
      error: err => console.log(err),
    });
  }

  saveAndHide() {
    this.saveEvent.emit();
    this.showModal = false;
  }
}
