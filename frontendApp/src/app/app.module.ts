import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { IonicStorageModule } from '@ionic/storage-angular';
import { RouteReuseStrategy } from '@angular/router';

import { IonicModule, IonicRouteStrategy } from '@ionic/angular';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import {
  HTTP_INTERCEPTORS,
  provideHttpClient,
  withInterceptorsFromDi,
  withJsonpSupport,
} from '@angular/common/http';

import { ReteModule } from 'rete-angular-plugin/21';
import { TransformNodeComponent } from './components/nodes/transform/nodes.component';
import { InputNodeComponent } from './components/nodes/input/nodes.component';
import { OutputNodeComponent } from './components/nodes/output/nodes.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { StatusComponentComponent } from './components/widgets/status-component/status-component.component';
import { MatTooltipModule } from '@angular/material/tooltip';
import { QueryBuilderModule } from 'ngx-query-builder';
import { AuthInterceptor } from './interceptors/auth.interceptor';
import { ErrorInterceptor } from './interceptors/error.interceptor';

@NgModule({
    declarations: [AppComponent],
    bootstrap: [AppComponent],
    imports: [
    BrowserModule,
    IonicModule.forRoot(),
    ReteModule,
    BrowserAnimationsModule,
    AppRoutingModule,
    IonicStorageModule.forRoot(),
    MatTooltipModule,
    QueryBuilderModule,
    TransformNodeComponent,
    OutputNodeComponent,
    InputNodeComponent,
    StatusComponentComponent,
],
    exports: [QueryBuilderModule],
    providers: [
        { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
        // Register HTTP Interceptors
        {
            provide: HTTP_INTERCEPTORS,
            useClass: AuthInterceptor,
            multi: true,
        },
        {
            provide: HTTP_INTERCEPTORS,
            useClass: ErrorInterceptor,
            multi: true,
        },
        provideHttpClient(withInterceptorsFromDi(), withJsonpSupport()),
    ],
})
export class AppModule {}
