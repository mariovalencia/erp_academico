import { ApplicationConfig } from '@angular/core';
import { appConfig as coreConfig } from './core/config/app.config';

export const appConfig: ApplicationConfig = {
  providers: [
    ...coreConfig.providers
  ]
};
