import { Component, inject, OnInit } from '@angular/core';
import { DashboardComponent } from '../dashboard/dashboard.component';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import {
  MatSnackBar,
} from '@angular/material/snack-bar';

interface CatalogItem {
  type: string;
  name: string;
  owner: {
    "name": string,
    "logo": string,
  };
}

interface BilateralContractsResponse {
  contracts: any[];
  endpoint: string;
  contractUri: string;
}

interface DataExchangeExecution{
  id: string;
  createdAt: string;
}

interface DataResource{
  id: string;
  name: string;
  description: string;
  owner: string;
}

interface DataExchange{
  executions: DataExchangeExecution[];
  resources: DataResource;
  contract: string;
  providerEndpoint?: string;
  consumerEndpoint?: string;
}

interface DataExchangeResponse{
  dataExchanges: DataExchange[];
}

@Component({
    selector: 'app-ptxdashboard',
    templateUrl: './ptxdashboard.component.html',
    styleUrls: ['./ptxdashboard.component.scss'],
    imports: [CommonModule, IonicModule]
})
export class PTXDashboardComponent  extends DashboardComponent implements OnInit{

  serviceOfferings: CatalogItem[] = [];
  softwareResources: CatalogItem[] = [];
  dataResources: CatalogItem[] = [];
  contractsBilaterals: any[] = [];
  contractsUseCase: any[] = [];
  pdcEndpoint: string = ''; 
  contractUri: string = '';
  private _snackBar = inject(MatSnackBar);
  isLoadingCatalog: boolean = true;
  dataExchanges: DataExchange[] = [];
  expandedExchanges: Set<number> = new Set();
  showAllExecutions: Set<number> = new Set();
  isLoadingHistory: boolean = true;

  constructor() {
    super();
  }

  ngOnInit(): void {
    this.loadCatalog();
    //this.loadContractsBilaterals();
    this.loadContractsUseCase();
    this.loadDataExchangeHistory();
  }

  loadCatalog() {
    this.isLoadingCatalog = true;
    this.http.get<{ catalog: CatalogItem[] }>(this.datasetService.urlBack + '/ptx/' + this.dataset.id).subscribe((res) => {
      this.serviceOfferings = res.catalog.filter(item => item.type === 'ptx:serviceofferings');
      this.softwareResources = res.catalog.filter(item => item.type === 'ptx:softwareresources');
      this.dataResources = res.catalog.filter(item => item.type === 'ptx:dataresources');
      this.isLoadingCatalog = false;
    })
  }

  loadContractsUseCase(){
    this.http.get(this.datasetService.urlBack + '/ptx/contracts/use-case/' + this.dataset.id).subscribe((res) => {
      this.contractsUseCase = res as any[];
    })
  }

  loadDataExchangeHistory() {
    this.isLoadingHistory = true;
    this.http.get<DataExchangeResponse>(`${this.datasetService.urlBack}/ptx/dataExchanges/${this.dataset.id}`)
    .subscribe({
      next: (res) => {
        this.dataExchanges = res.dataExchanges;
        this.isLoadingHistory = false;
        console.log('Data exchanges loaded:', this.dataExchanges);
      },
      error: (err) => {
        console.error('Failed to load data exchanges', err);
        this.isLoadingHistory = false;
      }
    });
  }

  triggerDataExchange(contract: any, provider, purpose) {
    const exchangeUrl = `${this.datasetService.urlBack}/ptx/trigger-data-exchange/${this.dataset.id}`;
    const purpose_url = "https://api.visionstrust.com/v1/catalog/serviceofferings/" + purpose._id;
    const resource_url = "https://api.visionstrust.com/v1/catalog/serviceofferings/" + provider._id;

    const payload = {
      "contract": contract._id,
      "purposeId": purpose_url,
      "resourceId": resource_url,
    }

    this.http.post(exchangeUrl, payload)
      .subscribe({
        next: (res: any) => {
          console.log('Exchange successful:', res);
          if (res.success) {
            this._snackBar.open('Data exchange triggered', 'x', {
              duration: 3000,
              horizontalPosition: 'start',
              verticalPosition: 'bottom',
              panelClass: ['success-snackbar']
            });
            this.datasetService.get();
          }
        },
        error: (err) => {
          this._snackBar.open('Data exchange trigger failed', 'x', {
            duration: 5000,
            horizontalPosition: 'start',
            verticalPosition: 'bottom',
            panelClass: ['error-snackbar']
          });
        }
      });
  }

  toggleShowAllExecutions(exchangeIndex: number) {
    if (this.showAllExecutions.has(exchangeIndex)) {
      this.showAllExecutions.delete(exchangeIndex);
    } else {
      this.showAllExecutions.add(exchangeIndex);
    }
  }

  isShowingAllExecutions(exchangeIndex: number): boolean {
    return this.showAllExecutions.has(exchangeIndex);
  }

  getExecutionsToShow(exchange: DataExchange, exchangeIndex: number): DataExchangeExecution[] {
    if (!exchange.executions) return [];
    
    if (this.isShowingAllExecutions(exchangeIndex)) {
      return exchange.executions;
    } else {
      return exchange.executions.slice(0, 10);
    }
  }

  shouldShowMoreButton(exchange: DataExchange): boolean {
    return exchange.executions && exchange.executions.length > 10;
  }

  getHiddenExecutionsCount(exchange: DataExchange): number {
    return exchange.executions ? Math.max(0, exchange.executions.length - 10) : 0;
  }

  toggleExchange(index: number) {
    if (this.expandedExchanges.has(index)) {
      this.expandedExchanges.delete(index);
    } else {
      this.expandedExchanges.add(index);
    }
  }

  isExchangeExpanded(index: number): boolean {
    return this.expandedExchanges.has(index);
  }

  getExecutionCount(exchange: DataExchange): number {
    return exchange.executions.length;
  }

  getLatestExecutionDate(exchange: DataExchange): string {
    if (!exchange.executions || exchange.executions.length === 0) {
      return 'No executions';
    }

    const sortedExecutions = exchange.executions
      .filter(exec => exec.createdAt)
      .sort((a, b) => new Date(b.createdAt!).getTime() - new Date(a.createdAt!).getTime());

    if (sortedExecutions.length === 0) {
      return '';
    }

    return new Date(sortedExecutions[0].createdAt!).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }


  /**
 * Formats a given date string into a human-readable format.
 * If the input is empty or invalid, returns 'N/A'.
 * 
 * @param dateString - The date string to format (ISO format expected)
 * @returns A formatted date string in 'dd MMM yyyy, HH:mm' format (French locale)
 */
  formatDate(dateString: string): string {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  getCardClass(type: string): string {
    if (type === 'ptx:serviceofferings') {
      return 'card-service';
    } else if (type === 'ptx:softwaresources') {
      return 'card-software';
    } else if (type === 'ptx:dataresources') {
      return 'card-data';
    }
    return 'card-default';
  }

  getSkeletonArray(count: number = 1): number[] {
    return Array(count).fill(0).map((x, i) => i);
  }

  loadContractsBilaterals() {
    this.http.get<BilateralContractsResponse>(`${this.datasetService.urlBack}/ptx/contracts/bilaterals/${this.dataset.id}`)
      .subscribe({
        next: (res) => {
          this.contractsBilaterals = res.contracts;
          //console.log('Bilateral contracts loaded:', this.contractsBilaterals);
          this.pdcEndpoint = res.endpoint;
          this.contractUri = res.contractUri;
        },
        error: (err) => {
          console.error('Failed to load bilateral contracts', err);
        }
      });
  }
}
