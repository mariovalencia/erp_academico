import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { MatSnackBar } from '@angular/material/snack-bar';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const snackBar = inject(MatSnackBar);

  return next(req).pipe(
    catchError((error) => {
      let errorMessage = 'Ocurrió un error inesperado';

      if (error.status === 0) {
        errorMessage = 'Error de conexión. Verifica tu internet.';
      } else if (error.status === 400) {
        errorMessage = error.error?.message || 'Solicitud inválida';
      } else if (error.status === 403) {
        errorMessage = 'No tienes permisos para esta acción';
      } else if (error.status === 404) {
        errorMessage = 'Recurso no encontrado';
      } else if (error.status === 500) {
        errorMessage = 'Error interno del servidor';
      }

      snackBar.open(errorMessage, 'Cerrar', {
        duration: 5000,
        horizontalPosition: 'right',
        verticalPosition: 'top',
        panelClass: ['error-snackbar']
      });

      return throwError(() => error);
    })
  );
};
