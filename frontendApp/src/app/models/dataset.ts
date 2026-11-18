import { DashboardComponent } from "../components/dashboards/dashboard/dashboard.component";
import { DatasetType } from "../enums/dataset-type";
import { DatasetsI } from "./datasets-i";
import { Folder } from "./folder";

export abstract class Dataset {
    id: string;
    name: string;
    description: string;
    parentFolder?: Folder;
    type: DatasetType;
    dashboardComponent: any = DashboardComponent
    // Ownership and sharing
    owner_id?: string;
    shared_with?: string[];

    constructor(dataset?: DatasetsI) {
        if (dataset) {
            this.id = dataset.id;
            this.name = dataset.name;
            this.description = dataset.description;
            this.parentFolder = dataset.parentFolder;
            this.type = dataset.type;
            this.owner_id = dataset.owner_id;
            this.shared_with = dataset.shared_with;
        }
    }
}
