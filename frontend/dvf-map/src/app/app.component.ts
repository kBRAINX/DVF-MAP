// src/app/app.component.ts
import { Component, inject } from "@angular/core"
import { CommonModule } from "@angular/common"
import { RouterOutlet } from "@angular/router"
import { FormComponent } from "./components/form/form.component"
import { MapService } from "./services/map.service"
import { MapComponent } from "./components/map/map.component"
import { NavbarComponent } from "./components/shared/navbar/navbar.component"
import { AuthService } from "./services/auth.service"
import { Observable } from "rxjs"

@Component({
  selector: "app-root",
  standalone: true,
  imports: [CommonModule, FormComponent, RouterOutlet, NavbarComponent],
  templateUrl: "./app.component.html",
  styleUrls: ["./app.component.scss"],
})
export class AppComponent {
  sidebarOpen = false
  mapType = "street"
  isAuthenticated$: Observable<boolean>

  private readonly mapService = inject(MapService)
  private readonly authService = inject(AuthService)

  constructor() {
    this.isAuthenticated$ = this.authService.isAuthenticated$
  }

  toggleSidebar(): void {
    this.sidebarOpen = !this.sidebarOpen
  }

  setMapType(type: "street" | "satellite" | "cadastre"): void {
    this.mapType = type
    this.mapService.setMapType(type)
  }

  centerMap(): void {
    this.mapService.centerMap()
  }
}
