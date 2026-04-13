import { Component, Input, OnInit } from '@angular/core';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { DatasetFile } from 'src/app/models/dataset-file';

@Component({
    selector: 'app-file-dashboard',
    templateUrl: './file-dashboard.component.html',
    styleUrls: ['./file-dashboard.component.scss'],
    standalone: false
})
export class FileDashboardComponent extends DashboardComponent implements OnInit {

  ifExistOptions = [
    { value: 'replace', label: 'Replace' },
    { value: 'append', label: 'Append' }
  ];
  @Input() override dataset: DatasetFile;

  constructor() {
    super();
  }

  ngOnInit() {
    // Initialiser la valeur par défaut si elle n'existe pas
    if (!this.dataset.ifExist) {
      this.dataset.ifExist = 'replace';
    }
  }

  onIfExistChange(value: 'replace' | 'append') {
    this.dataset.ifExist = value;
    this.onDatasetChange();
  }

  onDatasetChange() {
    // Sauvegarder les modifications côté serveur via le service dataset
    this.datasetService.editDataset(this.dataset).subscribe({
      next: (updatedDataset) => {
        console.log('Dataset updated successfully:', updatedDataset);
        // Optionnel : mettre à jour le dataset local avec la réponse du serveur
        // this.dataset = updatedDataset;
      },
      error: (error) => {
        console.error('Error updating dataset:', error);
        // Optionnel : gérer l'erreur (toast, rollback, etc.)
      }
    });
  }

  getDelimiterDisplay(delimiter: string): string {
    switch(delimiter) {
      case ',': return 'Comma (,)';
      case ';': return 'Semicolon (;)';
      case '\t': return 'Tab (\\t)';
      case '|': return 'Pipe (|)';
      default: return delimiter;
    }
  }

  formatFileSize(bytes: number): string {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  }

  getDatasetStatus(): string {
    if (!this.dataset.filePath) return 'incomplete';
    if (this.dataset.metadata) return 'complete';
    return 'partial';
  }

  getStatusIcon(): string {
    switch(this.getDatasetStatus()) {
      case 'complete': return 'check_circle';
      case 'partial': return 'warning';
      case 'incomplete': return 'error';
      default: return 'help';
    }
  }

  getDatasetStatusText(): string {
    switch(this.getDatasetStatus()) {
      case 'complete': return 'Dataset Ready';
      case 'partial': return 'Configuration Incomplete';
      case 'incomplete': return 'Dataset Not Configured';
      default: return 'Unknown Status';
    }
  }
}
