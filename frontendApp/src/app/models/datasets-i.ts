import { Component } from '@angular/core';
import { DatasetType } from './../enums/dataset-type';


import { Folder } from "./folder";
import { PTXDashboardComponent } from '../components/dashboards/ptxdashboard/ptxdashboard.component';

export interface DatasetsI {
    id: string;
    name: string;
    description: string;
    parentFolder: Folder;
    type: DatasetType;
    folder: string;
    inputType: string;
    filePath: string;
    csvHeader: string;
    csvDelimiter: string | null;
    file: File;
    uri: string;
    database: string;
    collection: string;
    host: string;
    user: string;
    password: string;
    table: string;
    url: string;
    index: string;
    authMode?: 'none' | 'basic' | 'apiKey' | 'bearer';
    verifyCerts?: boolean;
    key: string;
    bearerToken: string;
    apiAuth: string;
    clientId: string;
    clientSecret: string;
    authUrl: string;
    basicToken: string;
    metadata: {
        fileSize: string,
        fileType: string,
        modifTime: string,
        accessTime: string,
        columnCount: string,
        rowCount: string,
    }
    dashboard?: any
    service_key: string,
    secret_key: string,
    token: string,
    refreshToken: string
    ifExist?: 'replace' | 'append'; // Default behavior
    // Ownership and sharing
    owner_id?: string;
    shared_with?: string[];
}
