import { ChangeDetectorRef, Component, Input, OnChanges, SimpleChanges, inject } from "@angular/core";
import { ClassicPreset } from "rete";
import { IonicModule } from "@ionic/angular";

export interface textDisplayControlI{
    value: string,
    label?: string,
    copyable?: boolean;
}

export class TextDisplayControl extends ClassicPreset.Control implements textDisplayControlI{
    value: string;
    label?: string;
    copyable?: boolean;

    constructor(data: textDisplayControlI){
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
    imports: [IonicModule]
})
export class TextDisplayWidgetComponent implements OnChanges {
    @Input() data: TextDisplayControl;
    cdr = inject(ChangeDetectorRef);
  
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