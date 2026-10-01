import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App implements OnInit {
  title = 'hgw-dashboard';

  ngOnInit(): void {
    // Start in dark mode by default
    document.body.classList.add('app-dark');
  }
}