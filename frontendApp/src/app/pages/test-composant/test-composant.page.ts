import { Component, OnInit } from '@angular/core';

@Component({
    selector: 'app-test-composant',
    templateUrl: './test-composant.page.html',
    styleUrls: ['./test-composant.page.scss'],
    standalone: false
})
export class TestComposantPage implements OnInit {

  constructor() { }

  ngOnInit() {
  }

}
