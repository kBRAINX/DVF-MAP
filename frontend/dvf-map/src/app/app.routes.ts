import type { Routes } from "@angular/router";
import { MapComponent } from "./components/map/map.component";
import { LoginComponent } from "./components/auth/login/login.component";
import { RegisterComponent } from "./components/auth/register/register.component";
import { ProfileComponent } from "./components/auth/profile/profile.component";
import { AuthGuard } from "./guards/auth.guard";

export const routes: Routes = [
  {
    path: "",
    component: MapComponent,
    canActivate: [AuthGuard]
  },
  {
    path: "auth/login",
    component: LoginComponent
  },
  {
    path: "auth/register",
    component: RegisterComponent
  },
  {
    path: "profile",
    component: ProfileComponent,
    canActivate: [AuthGuard]
  },
  {
    path: "**",
    redirectTo: ""
  },
];
