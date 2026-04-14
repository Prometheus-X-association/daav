import { Component, OnDestroy, Input} from '@angular/core';
import {  Subject } from 'rxjs';
import { CdkDragDrop, moveItemInArray} from '@angular/cdk/drag-drop';
import { Column, ColumnMapping, DatasetMapper } from 'src/app/models/data-mapper-types';



@Component({
    selector: 'app-data-mapper',
    templateUrl: './data-mapper.component.html',
    styleUrls: ['./data-mapper.component.scss'],
    standalone: false
})
export class DataMapperComponent implements  OnDestroy {
  private destroy$ = new Subject<void>();

  @Input()datasets: DatasetMapper[] = [];
  @Input() mappings: ColumnMapping[] = [];
  draggedColumn: Column | null = null;
  activeMapping: string | null = null;


  constructor() {}

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  getConnectedLists(): string[] {
    const mappingIds = this.mappings.map(m => 'mapping-' + m.id);
    return ['mapping-dropzone', ...mappingIds];
  }

  onDragStart(event: any, column: Column) {
    this.draggedColumn = column;
    this.setDraggedColumn(column);
  }

  onDragEnd() {

    this.setActiveMapping(null);
    this.cleanupAfterDrop();
  }

  onDrop(event: CdkDragDrop<any[]>, targetMappingId?: string) {
    // Récupérer la colonne depuis l'événement de drag
    const column = event.item.data as Column;

    if (event.previousContainer === event.container) {
      moveItemInArray(event.container.data, event.previousIndex, event.currentIndex);
    } else {
      if (targetMappingId) {
        // Ajouter à un mapping existant
        const mapping = this.mappings.find(m => m.id === targetMappingId);
        if (mapping) {
          mapping.sources.push(column);
        }
      } else {
        // Créer un nouveau mapping
        this.addMapping({
          id: crypto.randomUUID(),
          sources: [column],
          targetName: column.name
        });
      }
    }
  }

  private cleanupAfterDrop() {
    // Nettoyer l'état après un drop réussi
    this.draggedColumn = null;
    this.setDraggedColumn(null);
    this.setActiveMapping(null);
  }

  isColumnMapped(column: Column): boolean {
    return this.mappings.some(m => m.sources.some(s => s.id === column.id));
  }

  getDatasetName(datasetId: string): string {
    return this.datasets.find(d => d.id === datasetId)?.name || '';
  }

  setDraggedColumn(column: Column | null) {
    this.draggedColumn=column;
  }

  setActiveMapping(mappingId: string | null) {
    this.activeMapping=mappingId;
  }

  addMapping(mapping: ColumnMapping) {
    this.mappings.push(mapping);
  }

  removeMapping(mappingId: string) {
    this.mappings.splice(this.mappings.findIndex(m => m.id === mappingId), 1);
  }

  removeSourceFromMapping(mappingId: string, columnId: string) {
    const mapping = this.mappings.find(m => m.id === mappingId);
    if (mapping) {
      mapping.sources.splice(mapping.sources.findIndex(s => s.id === columnId), 1);
      if (mapping.sources.length === 0) {
        this.mappings.splice(this.mappings.findIndex(m => m.id === mappingId), 1);
      }
    }
  }

  // État de collapse pour chaque dataset
  collapsedSections: { [key: string]: boolean } = {};

  toggleSection(sectionKey: string): void {
    this.collapsedSections[sectionKey] = !this.collapsedSections[sectionKey];
  }

  isSectionCollapsed(sectionKey: string): boolean {
    return this.collapsedSections[sectionKey] || false;
  }
}
