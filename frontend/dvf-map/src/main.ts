import { bootstrapApplication } from '@angular/platform-browser';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {importProvidersFrom, inject} from '@angular/core';
import { ReactiveFormsModule } from '@angular/forms';

import { AppComponent } from './app/app.component';
import { routes } from './app/app.routes';
import { AuthService } from './app/services/auth.service';
import { Router } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { catchError, throwError } from 'rxjs';

bootstrapApplication(AppComponent, {
  providers: [
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([
        (req, next) => {
          const authService = inject(AuthService);
          const router = inject(Router);

          const token = authService.getToken();

          let authReq = req;
          if (token) {
            authReq = req.clone({
              headers: req.headers.set('Authorization', `Bearer ${token}`)
            });
          }

          return next(authReq).pipe(
            catchError((error: HttpErrorResponse) => {
              if (error.status === 401) {
                authService.logout();
                router.navigate(['/auth/login']);
              }
              return throwError(() => error);
            })
          );
        }
      ])
    ),
    importProvidersFrom(ReactiveFormsModule)
  ]
}).catch(err => console.error(err));
