// Importation des décorateurs et classes nécessaires
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, map, of } from 'rxjs';
import { DvfProperty } from '../models/dvf-property.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root' // Fournit ce service à l'échelle de toute l'application
})
export class DvfService {
  constructor(private readonly http: HttpClient) {}

  /**
   * Méthode principale pour récupérer les propriétés DVF filtrées
   * @param topLeft Coin supérieur gauche de la zone visible sur la carte
   * @param bottomRight Coin inférieur droit de la zone visible
   * @param priceRange Plage de prix : [min, max] ou null si non utilisé
   * @param dateRange Plage de dates : [start, end] ou null
   * @param exactDate Date exacte à filtrer si utilisée
   * @returns Observable contenant une liste de DvfProperty[]
   */
  getDvfProperties(
    topLeft: [number, number],
    bottomRight: [number, number],
    priceRange: [number, number] | null,
    dateRange: [string, string] | null,
    exactDate: string | null = null
  ): Observable<DvfProperty[]> {
    // Construction des paramètres de requête API
    const params: any = {
      topLeft: topLeft.join(','),           // Format: "lat,lng"
      bottomRight: bottomRight.join(',')    // Format: "lat,lng"
    };

    // Ajout de la plage de prix si présente
    if (priceRange) {
      params.price = `${priceRange[0]},${priceRange[1]}`;
    }

    // Si une date exacte est fournie, elle est prioritaire sur la plage
    if (exactDate) {
      params.date = exactDate;
    } else if (dateRange) {
      params.date = `${dateRange[0]},${dateRange[1]}`;
    }

    // URL de l'endpoint backend, basé sur l'environnement
    const apiUrl = `${environment.apiUrl}/dvf/ventes`;

    // Affichage de l'URL finale avec les paramètres pour debug
    console.log('📡 API URL:', `${apiUrl}?${new URLSearchParams(params).toString()}`);

    // Appel HTTP GET à l'API avec transformation de réponse
    return this.http.get<any[]>(apiUrl, { params }).pipe(
      // Transformation des données brutes en objets `DvfProperty`
      map(data => {
        if (!Array.isArray(data)) return [];

        return data.map(item => {
          const latitude = parseFloat(item.latitude);
          const longitude = parseFloat(item.longitude);
          const valeur = parseFloat(item.valeur_fonciere);

          // Retourne un objet typé DvfProperty
          return {
            id_mutation: item.id_mutation ?? '',
            date_mutation: item.date_mutation ?? '',
            valeur_fonciere: isNaN(valeur) ? 0 : valeur,
            type_local: 'Maison',
            latitude: isNaN(latitude) ? 0 : latitude,
            longitude: isNaN(longitude) ? 0 : longitude,
            adresse_numero: item.adresse_numero ?? '',
            adresse_nom_voie: item.adresse_nom_voie ?? '',
            code_postal: item.code_postal ?? '',
            nom_commune: item.nom_commune ?? '',
            id_parcelle: item.id_parcelle ?? '',

            surface_terrain: item.surface_terrain ?? undefined,
            surface: item.surface_reelle_bati ?? undefined
          } as DvfProperty;
        });
      }),
      // Gestion des erreurs : log console + retour d’une liste vide
      catchError(error => {
        console.error('❌ Erreur API DVF:', error);
        return of([]); // Retourne un observable vide pour éviter l’arrêt du flux
      })
    );
  }
}
