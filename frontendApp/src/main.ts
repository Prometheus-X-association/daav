import { enableProdMode, provideZoneChangeDetection, importProvidersFrom } from '@angular/core';
import { environment } from './environments/environment';
import { PreloadAllModules, provideRouter, RouteReuseStrategy, withPreloading } from '@angular/router';
import { IonicRouteStrategy, IonicModule } from '@ionic/angular';
import { HTTP_INTERCEPTORS, provideHttpClient, withInterceptorsFromDi, withJsonpSupport } from '@angular/common/http';
import { AuthInterceptor } from './app/interceptors/auth.interceptor';
import { ErrorInterceptor } from './app/interceptors/error.interceptor';
import { BrowserModule, bootstrapApplication } from '@angular/platform-browser';
import { ReteModule } from 'rete-angular-plugin/21';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { routes } from './app/app.routes';
import { IonicStorageModule } from '@ionic/storage-angular';
import { MatTooltipModule } from '@angular/material/tooltip';
import { QueryBuilderModule } from 'ngx-query-builder';
import { AppComponent } from './app/app.component';

if (environment.production) {
  enableProdMode();
}

bootstrapApplication(AppComponent, {
    providers: [
        // Angular 21 is zoneless by default: the application relies on Zone.js change detection
        provideZoneChangeDetection(),
        importProvidersFrom(BrowserModule, IonicModule.forRoot(), ReteModule, BrowserAnimationsModule, IonicStorageModule.forRoot(), MatTooltipModule, QueryBuilderModule),
        provideRouter(routes, withPreloading(PreloadAllModules)),
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
    ]
})
  .catch(err => console.log(err));
