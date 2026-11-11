import { ChangeDetectorRef, Component, Input, OnChanges, SimpleChanges, inject } from "@angular/core";
import { ClassicPreset } from "rete";
import { IonButton, IonIcon } from "@ionic/angular/standalone";
import { addIcons } from "ionicons";
import { copyOutline } from "ionicons/icons";

export interface TextDisplayControlI{
    value: string,
    label?: string,
    copyable?: boolean;
}

export class TextDisplayControl extends ClassicPreset.Control implements TextDisplayControlI{
    value: string;
    label?: string;
    copyable?: boolean;

    constructor(data: TextDisplayControlI){
        super();
        if(data){
            this.value = data.value;
            this.label = data.label || null;
            this.copyable = data.copyable || false;
        }
    }
    
    copyToClipboard(text: string, event?: Event) {
        if (event) {
            event.preventDefault();
            event.stopPropagation();
          }
          
          if (this.copyable && navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
            }).catch(err => {
              console.error('Failed to copy text: ', err);
            });
          }
    }
}

@Component({
    selector: "app-text-display-widget",
    templateUrl: "./text-display-widget.component.html",
    styleUrls: ['./text-display-widget.component.scss'],
    imports: [IonButton, IonIcon]
})
export class TextDisplayWidgetComponent implements OnChanges {
    @Input() data: TextDisplayControl;
    cdr = inject(ChangeDetectorRef);
  
    constructor() {
        addIcons({ copyOutline });
    }

    ngOnChanges(changes: SimpleChanges): void {
      this.cdr.detectChanges();
    }

    onCopy(text: string, event: Event) {
        event.stopPropagation();
        if (this.data.copyable) {
            this.data.copyToClipboard(text, event);
        }
    }
  }