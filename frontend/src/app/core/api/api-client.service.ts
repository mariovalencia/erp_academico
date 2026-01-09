import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../environments/environment';

export interface ApiOptions {
  headers?: HttpHeaders;
  params?: any;
  responseType?: any;
}

@Injectable({ providedIn: 'root' })
export class ApiClientService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrl;

  private getOptions(options?: ApiOptions): any {
    return {
      headers: options?.headers,
      params: options?.params ? new HttpParams({ fromObject: options.params }) : undefined,
      responseType: options?.responseType
    };
  }

  get<T>(endpoint: string, options?: ApiOptions) {
    return this.http.get<T>(`${this.baseUrl}${endpoint}`, this.getOptions(options));
  }

  post<T>(endpoint: string, data: any, options?: ApiOptions) {
    return this.http.post<T>(`${this.baseUrl}${endpoint}`, data, this.getOptions(options));
  }

  put<T>(endpoint: string, data: any, options?: ApiOptions) {
    return this.http.put<T>(`${this.baseUrl}${endpoint}`, data, this.getOptions(options));
  }

  patch<T>(endpoint: string, data: any, options?: ApiOptions) {
    return this.http.patch<T>(`${this.baseUrl}${endpoint}`, data, this.getOptions(options));
  }

  delete<T>(endpoint: string, options?: ApiOptions) {
    return this.http.delete<T>(`${this.baseUrl}${endpoint}`, this.getOptions(options));
  }
}
