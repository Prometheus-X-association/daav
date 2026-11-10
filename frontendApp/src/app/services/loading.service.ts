import { Injectable, signal } from '@angular/core';
import { Observable, concatMap, finalize, of, tap } from 'rxjs';

// @Injectable({
//   providedIn: 'root'
// })
@Injectable()
export class LoadingService {
  loading = signal<boolean>(false);
  constructor(){}
  showLoaderUntilCompleted<T>(obs$: Observable<T>): Observable<T> {
    return of(null)
            .pipe(
              tap(() => this.loadingOn()),
              concatMap(() => obs$),
              finalize(() => this.loadingOff())
            )
  }

  loadingOn(){
    this.loading.set(true);
  }
  
  loadingOff(){
    this.loading.set(false);
  }
}
