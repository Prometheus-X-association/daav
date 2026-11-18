import { MysqlDashboardComponent } from "../components/dashboards/mysql-dashboard/mysql-dashboard.component";
import { DatasetType } from "../enums/dataset-type";
import { Dataset } from "./dataset";
import { DatasetsI } from "./datasets-i";

export class DatasetMySQL extends Dataset {
    host: string;
    user: string;
    password: string;
    database: string;
    table: string;

    constructor(dataset?: DatasetsI) {
        super(dataset);
        this.type = DatasetType.MySQL;
        this.dashboardComponent = MysqlDashboardComponent;
        if (dataset) {
            this.host = dataset.host;
            this.user = dataset.user;
            this.password = dataset.password;
            this.database = dataset.database;
            this.table = dataset.table;
        }
    }
}
