import { ElasticDashboardComponent } from "../components/dashboards/elastic-dashboard/elastic-dashboard.component";
import { DatasetType } from "../enums/dataset-type";
import { Dataset } from "./dataset";
import { DatasetsI } from "./datasets-i";

export type ElasticAuthMode = 'none' | 'basic' | 'apiKey' | 'bearer';

export class DatasetElasticSearch extends Dataset {
    url: string;
    user: string;
    password: string;
    index: string;
    key: string;
    bearerToken: string;
    authMode: ElasticAuthMode;
    verifyCerts: boolean;

    constructor(dataset?: DatasetsI) {
        super(dataset);
        this.type = DatasetType.ElasticSearch;
        this.dashboardComponent = ElasticDashboardComponent;
        if (dataset) {
            this.url = dataset.url;
            this.user = dataset.user;
            this.password = dataset.password;
            this.index = dataset.index;
            this.key = dataset.key;
            this.bearerToken = dataset.bearerToken;
            this.authMode = dataset.authMode;
            this.verifyCerts = dataset.verifyCerts ?? true;
        }
    }
}
