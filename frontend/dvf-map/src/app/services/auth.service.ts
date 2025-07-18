// src/app/services/auth.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, map, catchError, throwError } from 'rxjs';

export interface User {
  id: number;
  email: string;
  firstName?: string;
  lastName?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface AuthResponse {
  id: number;
  email: string;
  firstName?: string;
  lastName?: string;
  token: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  firstName?: string;
  lastName?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:3000/api/auth'; // Url de l'API

  private currentUserSubject = new BehaviorSubject<User | null>(this.getUserFromStorage());
  public currentUser$ = this.currentUserSubject.asObservable();

  private isAuthenticatedSubject = new BehaviorSubject<boolean>(this.hasValidToken());
  public isAuthenticated$ = this.isAuthenticatedSubject.asObservable();

  constructor() {
    // Vérifier la validité du token au démarrage
    this.checkTokenValidity();
  }

  // Connexion utilisateur
  login(credentials: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials)
      .pipe(
        map(response => {
          this.setSession(response);
          return response;
        }),
        catchError(error => throwError(() => error))
      );
  }

  // Inscription utilisateur
  register(userData: RegisterRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/register`, userData)
      .pipe(
        map(response => {
          this.setSession(response);
          return response;
        }),
        catchError(error => throwError(() => error))
      );
  }

  // Récupérer le profil utilisateur
  getProfile(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/profile`)
      .pipe(
        map(user => {
          this.currentUserSubject.next(user);
          return user;
        }),
        catchError(error => throwError(() => error))
      );
  }

  // Déconnexion
  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    this.currentUserSubject.next(null);
    this.isAuthenticatedSubject.next(false);
  }

  // Obtenir l'utilisateur actuel
  getCurrentUser(): User | null {
    return this.currentUserSubject.value;
  }

  // Vérifier si l'utilisateur est connecté
  isAuthenticated(): boolean {
    return this.isAuthenticatedSubject.value;
  }

  // Obtenir le token
  getToken(): string | null {
    return localStorage.getItem('token');
  }

  // Configurer la session après connexion/inscription
  private setSession(authResponse: AuthResponse): void {
    const user: User = {
      id: authResponse.id,
      email: authResponse.email,
      firstName: authResponse.firstName,
      lastName: authResponse.lastName
    };

    localStorage.setItem('token', authResponse.token);
    localStorage.setItem('user', JSON.stringify(user));

    this.currentUserSubject.next(user);
    this.isAuthenticatedSubject.next(true);
  }

  // Récupérer l'utilisateur depuis le localStorage
  private getUserFromStorage(): User | null {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        localStorage.removeItem('user');
      }
    }
    return null;
  }

  // Vérifier si le token est présent
  private hasValidToken(): boolean {
    const token = localStorage.getItem('token');
    return !!token;
  }

  // Vérifier la validité du token (optionnel : vérification avec le backend)
  private checkTokenValidity(): void {
    if (this.hasValidToken()) {
      // Optionnel : vérifier avec le backend si le token est valide
      this.getProfile().subscribe({
        next: () => {
          this.isAuthenticatedSubject.next(true);
        },
        error: () => {
          this.logout();
        }
      });
    }
  }
}
