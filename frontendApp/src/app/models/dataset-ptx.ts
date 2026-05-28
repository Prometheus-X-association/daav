import { PTXDashboardComponent } from "../components/dashboards/ptxdashboard/ptxdashboard.component";
import { DatasetType } from "../enums/dataset-type";
import { Dataset } from "./dataset";
import { DatasetsI } from "./datasets-i";

export class DatasetPTX extends Dataset{
    public token: string;
    public refreshToken: string;
    public url: string;
    public service_key: string;
    public secret_key: string;

    constructor(dataset?: DatasetsI) {
        super(dataset);
        this.type = DatasetType.PTX;
        this.dashboardComponent = PTXDashboardComponent;
        if (dataset) {
            this.url = dataset.url;
            this.token = dataset.token;
            this.refreshToken = dataset.refreshToken;
            this.service_key = dataset.service_key;
            this.secret_key = dataset.secret_key;
        }
    }
}
