import { Injectable } from "@angular/core"
import { BehaviorSubject, type Observable, Subject } from "rxjs"

// Interface décrivant les 4 coins visibles d'une carte
export interface MapCoordinates {
  topLeft: [number, number]
  topRight: [number, number]
  bottomLeft: [number, number]
  bottomRight: [number, number]
}

// Interface pour les bounds utilisés par l'API
export interface MapBounds {
  topLeft: [number, number]
  bottomRight: [number, number]
}

@Injectable({
  providedIn: "root", // Service singleton injecté globalement dans l'application
})
export class MapService {
  // Coordonnées actuelles de la carte (ex : après déplacement ou zoom)
  private readonly coordinatesSubject = new BehaviorSubject<MapCoordinates>({
    topLeft: [0, 0],
    topRight: [0, 0],
    bottomLeft: [0, 0],
    bottomRight: [0, 0],
  })

  // Subject pour signaler qu'un rafraîchissement de la carte est nécessaire
  private readonly refreshSubject = new Subject<void>()

  // Subject pour signaler un changement de type de carte (rue, satellite, cadastre)
  private readonly mapTypeSubject = new Subject<"street" | "satellite" | "cadastre">()

  // Subject pour demander un recentrage de la carte
  private readonly centerMapSubject = new Subject<void>()

  // Référence vers l'objet Leaflet map pour accéder aux bounds
  private leafletMap: any = null

  constructor() {}

  // ===== NOUVELLES MÉTHODES POUR L'INTÉGRATION API =====

  /**
   * NOUVELLE MÉTHODE : Stocker la référence vers la map Leaflet
   * À appeler depuis MapComponent après initialisation de la carte
   */
  setLeafletMap(map: any): void {
    this.leafletMap = map
  }

  /**
   * NOUVELLE MÉTHODE : Récupérer les bounds actuels de la carte
   * Utilisé par FormService pour les requêtes API
   */
  getCurrentBounds(): MapBounds | null {
    if (!this.leafletMap) {
      console.warn('⚠️ MapService - Aucune map Leaflet configurée')
      return null
    }

    try {
      const bounds = this.leafletMap.getBounds()
      const northeast = bounds.getNorthEast()
      const southwest = bounds.getSouthWest()

      const mapBounds: MapBounds = {
        topLeft: [northeast.lat, southwest.lng],
        bottomRight: [southwest.lat, northeast.lng]
      }

      return mapBounds

    } catch (error) {
      console.error('❌ MapService - Erreur lors de la récupération des bounds:', error)
      return null
    }
  }

  /**
   * NOUVELLE MÉTHODE : Mettre à jour les marqueurs sur la carte
   * Appelé depuis FormService après recherche
   */
  updateMarkers(properties: any[]): void {

    // Émettre un événement pour que MapComponent mette à jour ses marqueurs
    // On utilise le système existant de refresh
    this.refreshSubject.next()

    // Optionnel : stocker les propriétés pour usage ultérieur
    this.storeProperties(properties)
  }

  /**
   * Stocker les propriétés pour usage dans d'autres composants
   */
  private propertiesSubject = new BehaviorSubject<any[]>([])

  private storeProperties(properties: any[]): void {
    this.propertiesSubject.next(properties)
  }

  /**
   * Observable pour accéder aux propriétés stockées
   */
  getPropertiesObservable(): Observable<any[]> {
    return this.propertiesSubject.asObservable()
  }

  // ===== MÉTHODES EXISTANTES =====

  // Convertit des coordonnées WGS84 (lat, lng) en Lambert93 (x, y) – version simplifiée
  toLambert93(lat: number, lng: number): [number, number] {
    const x = lng * 100000 // Approche simplifiée : Longitude -> X Lambert93
    const y = lat * 100000 // Latitude -> Y Lambert93
    return [x, y]
  }

  // Convertit des coordonnées Lambert93 en WGS84 – version simplifiée
  fromLambert93(x: number, y: number): [number, number] {
    const lat = y / 100000
    const lng = x / 100000
    return [lat, lng]
  }

  // Définit les nouvelles coordonnées visibles de la carte
  setCoordinates(coordinates: MapCoordinates): void {
    this.coordinatesSubject.next(coordinates)
  }

  // Renvoie la dernière valeur des coordonnées de carte (sans observable)
  getCoordinates(): MapCoordinates {
    return this.coordinatesSubject.value
  }

  // Observable pour être notifié des changements de coordonnées
  getCoordinatesObservable(): Observable<MapCoordinates> {
    return this.coordinatesSubject.asObservable()
  }

  // Déclenche un événement pour rafraîchir la carte (utilisé par le formulaire)
  refreshMap(): void {
    this.refreshSubject.next()
  }

  // Permet aux autres composants de s'abonner aux événements de rafraîchissement
  getRefreshObservable(): Observable<void> {
    return this.refreshSubject.asObservable()
  }

  // Déclenche un changement de type de carte (utilisé dans le formulaire ou boutons)
  setMapType(type: "street" | "satellite" | "cadastre"): void {
    this.mapTypeSubject.next(type)
  }

  // Permet de s'abonner aux changements de type de carte
  getMapTypeObservable(): Observable<"street" | "satellite" | "cadastre"> {
    return this.mapTypeSubject.asObservable()
  }

  // Déclenche une action pour recentrer la carte (centrer sur un point, etc.)
  centerMap(): void {
    this.centerMapSubject.next()
  }

  // Permet de réagir lorsqu'on demande un recentrage de la carte
  getCenterMapObservable(): Observable<void> {
    return this.centerMapSubject.asObservable()
  }
}
