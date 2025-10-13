import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LoginComponent } from './components/login/login';

@Component({
  selector: 'app-root',
  imports: [CommonModule, LoginComponent],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App {
  protected readonly title = signal('frontend');
}
