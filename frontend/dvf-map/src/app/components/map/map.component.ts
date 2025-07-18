// Importation des modules Angular et Leaflet nécessaires
import { Component, type AfterViewInit, type OnDestroy, ViewChild, type ElementRef, inject } from "@angular/core"
import { CommonModule } from "@angular/common"
import * as L from "leaflet"
import { HttpClient } from "@angular/common/http"
import type { Subscription } from "rxjs"
import type { DvfProperty } from "../../models/dvf-property.model"
import { MapService } from "../../services/map.service"
import { DvfService } from "../../services/dvf.service"
import { FormService } from "../../services/form.service"

@Component({
  selector: "app-map", // Sélecteur HTML du composant
  standalone: true,
  imports: [CommonModule], // Importation du module commun Angular
  styleUrls: ["./map.component.scss"], // Fichier de style
  templateUrl: "./map.component.html", // Fichier HTML associé
})
export class MapComponent implements AfterViewInit, OnDestroy {
  @ViewChild("map") private readonly mapContainer!: ElementRef // Référence DOM vers la div contenant la carte
  private map: any // Objet Leaflet de la carte
  private markers: L.Marker[] = [] // Liste des marqueurs Leaflet affichés
  private fetchDataTimeout: any // Timer pour délai de chargement différé
  private baseLayers: any = {} // Couches de fond disponibles
  private currentLayer: any = null // Couche actuellement affichée

  public showProperties = true // Contrôle l’affichage des propriétés
  public usePriceFilter = false // État du filtre de prix
  public useDateFilter = false // État du filtre de date
  public minPrice = 0 // Prix minimum (filtre)
  public maxPrice = 2000000 // Prix maximum (filtre)
  public startDate = "2020-01-01" // Date de début (filtre)
  public endDate = "2023-12-31" // Date de fin (filtre)
  public visibleProperties: DvfProperty[] = [] // Propriétés visibles sur la carte
  public selectedPropertyIndex: number | null = null // Index de la propriété sélectionnée dans la table
  public tableCollapsed = false // État replié ou non de la table
  public isLoading = false // Indique si les données sont en cours de chargement
  public mapType = "street" // Type de fond de carte utilisé
  public dateMode = 'exact' // Mode de filtre date : exact ou intervalle
  public exactDate = '' // Valeur pour date exacte

  // Injection des services nécessaires
  private readonly mapService = inject(MapService)
  private readonly dvfService = inject(DvfService)
  private readonly formService = inject(FormService)
  private readonly http = inject(HttpClient)
  private readonly subscriptions: Subscription[] = [] // Liste des abonnements RxJS à nettoyer

  // Indique si au moins un filtre est activé
  get isFilterActive(): boolean {
    return this.usePriceFilter || this.useDateFilter
  }

  // Vérifie les filtres et déclenche un fetch si nécessaire
  private checkAndFetchIfNeeded(): void {
    if (this.usePriceFilter || this.useDateFilter) {
      this.fetchDvfData()
    } else {
      this.clearMarkers()
      this.visibleProperties = []
      console.log("✅ Tous les filtres désactivés — pas de requête API")
    }
  }

  ngAfterViewInit(): void {
    this.initMap() // Initialisation de la carte

    // Abonnement aux événements de rafraîchissement et aux changements de filtres
    this.subscriptions.push(
      this.mapService.getRefreshObservable().subscribe(() => this.fetchDvfData()),

      this.formService.getPriceFilterObservable().subscribe((filter) => {
        if (filter) {
          const [min, max] = filter
          this.minPrice = min
          this.maxPrice = max
          this.usePriceFilter = true
          this.fetchDvfData()
        } else {
          this.usePriceFilter = false
          this.minPrice = 0
          this.maxPrice = 0
          this.checkAndFetchIfNeeded()
        }
      }),

      this.formService.getDateFilterObservable().subscribe((filter) => {
        if (filter) {
          const [start, end] = filter
          this.startDate = start
          this.endDate = end
          this.useDateFilter = true
          this.fetchDvfData()
        } else {
          this.useDateFilter = false
          this.startDate = ''
          this.endDate = ''
          this.exactDate = ''
          this.checkAndFetchIfNeeded()
        }
      }),

      // Changement du type de carte (street, satellite, cadastre)
      this.mapService.getMapTypeObservable().subscribe((type) => {
        this.setMapType(type)
      }),
    )
  }

  ngOnDestroy(): void {
    // Nettoyage des abonnements et du timeout
    this.subscriptions.forEach((sub) => sub.unsubscribe())
    if (this.map) this.map.remove()
    if (this.fetchDataTimeout) clearTimeout(this.fetchDataTimeout)
  }

  private initMap(): void {
    // Création et configuration initiale de la carte Leaflet
    this.map = L.map(this.mapContainer.nativeElement, {
      center: [47.2184, -1.5536],
      zoom: 11,
    });

    // Définition des couches de fond disponibles
    this.baseLayers = {
      street: L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19,
      }),
      satellite: L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
        attribution: "",
        maxZoom: 19,
      }),
      cadastre: L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
        attribution: "",
        subdomains: "abcd",
        maxZoom: 19,
      }),
    }

    // Ajout de la couche street par défaut
    this.currentLayer = this.baseLayers.street.addTo(this.map)

    // Déclenche un fetch quand l'utilisateur bouge ou zoome sur la carte (si filtres actifs)
    this.map.on("moveend", () => {
      if (this.usePriceFilter || this.useDateFilter) {
        this.fetchDvfData()
      } else {
        this.clearMarkers()
        this.visibleProperties = []
        console.log("❌ Mouvement carte ignoré — aucun filtre actif")
      }
    })

    this.map.on("zoomend", () => {
      if (this.usePriceFilter || this.useDateFilter) {
        this.fetchDvfData()
      } else {
        this.clearMarkers()
        this.visibleProperties = []
        console.log("❌ Zoom ignoré — aucun filtre actif")
      }
    })

    // Chargement initial des données
    this.fetchDvfData()

    // Correction du rendu initial de la carte
    setTimeout(() => {
      if (this.map) {
        this.map.invalidateSize()
      }
    }, 300)
  }

  // Change dynamiquement le type de fond de carte affiché
  setMapType(type: string): void {
    if (!this.map || !this.baseLayers) return
    this.mapType = type

    // Retirer la couche précédente
    if (this.currentLayer) {
      this.map.removeLayer(this.currentLayer)
    }

    // Ajouter la nouvelle couche selon le type
    if (type === "satellite" && this.baseLayers.satellite) {
      this.currentLayer = this.baseLayers.satellite.addTo(this.map)
    } else if (type === "cadastre" && this.baseLayers.cadastre) {
      this.currentLayer = this.baseLayers.cadastre.addTo(this.map)
    } else {
      this.currentLayer = this.baseLayers.street.addTo(this.map)
    }
  }

  private fetchDvfData(): void {
    // Ne rien faire si aucun filtre n'est actif
    if (!this.usePriceFilter && !this.useDateFilter) {
      console.log("⛔ Aucun filtre activé - skip refresh")
      return
    }

    // Nettoyage des anciens marqueurs
    this.clearMarkers()
    this.visibleProperties = []

    // Utilise un délai pour éviter les requêtes multiples trop rapides
    if (this.fetchDataTimeout) clearTimeout(this.fetchDataTimeout)
    this.fetchDataTimeout = setTimeout(() => this.loadDvfData(), 300)
  }

  private loadDvfData(): void {
    // Vérifie que l'affichage est activé et qu’au moins un filtre est actif
    if (!this.showProperties || (!this.usePriceFilter && !this.useDateFilter)) {
      console.log("❌ Aucune requête envoyée — aucun filtre activé.")
      return
    }

    this.isLoading = true

    // Récupère les coordonnées de la carte visible
    const bounds = this.map.getBounds()
    const topLeft: [number, number] = [bounds.getNorthEast().lat, bounds.getNorthEast().lng]
    const bottomRight: [number, number] = [bounds.getSouthWest().lat, bounds.getSouthWest().lng]

    // Préparation des paramètres de filtre
    const price: [number, number] | null = this.usePriceFilter ? [this.minPrice, this.maxPrice] : null
    const date: [string, string] | null = this.useDateFilter ? [this.startDate, this.endDate] : null
    const exactDate: string | null = this.useDateFilter && this.dateMode === 'exact' ? this.exactDate : null

    // Requête vers l’API via le service
    this.dvfService.getDvfProperties(topLeft, bottomRight, price, date, exactDate).subscribe({
      next: (properties: DvfProperty[]) => {
        console.log(`🟢 ${properties.length} propriétés reçues`)
        this.clearMarkers()
        this.visibleProperties = properties

        // Ajoute un marqueur pour chaque propriété
        properties.forEach((property) => {
          if (property.latitude && property.longitude) {
            this.addMarker(property)
          }
        })
        this.isLoading = false

        // Réajuste l’affichage de la carte
        setTimeout(() => {
          if (this.map) {
            this.map.invalidateSize()
          }
        }, 300)
      },
      error: (err) => {
        console.error("❌ Erreur chargement DVF:", err)
        this.isLoading = false
      },
    })
  }

  private clearMarkers(): void {
    // Supprime tous les marqueurs de la carte
    this.markers.forEach((marker) => marker.remove())
    this.markers = []
  }

  private addMarker(property: DvfProperty): void {
    // Convertit les coordonnées et prépare l'affichage du prix
    const lat = Number(property.latitude)
    const lng = Number(property.longitude)
    const price = Math.round(Number(property.valeur_fonciere)).toLocaleString()

    // Format de la date pour l'affichage
    const date = property.date_mutation?.toString().split("-")
    const formattedDate = date && date.length === 3 ? `${date[2]}/${date[1]}/${date[0].slice(2)}` : property.date_mutation

    // Création d'un marqueur personnalisé
    const marker = L.marker([lat, lng], {
      icon: L.divIcon({
        className: "custom-marker",
        html: `
          <div class="marker-label red-x">
            <span class="price">${price} €</span>
          </div>
        `,
        iconSize: [90, 50],
        iconAnchor: [45, 25],
      }),
    }).addTo(this.map)

    // Ajoute une popup avec les détails
    marker.bindPopup(`
      <div class="property-popup">
        <h3>${price} €</h3>
        <p><strong>Date:</strong> ${formattedDate}</p>
        <p><strong>Adresse:</strong> ${property.adresse_numero ?? ""} ${property.adresse_nom_voie ?? ""}</p>
        <p><strong>Code postal:</strong> ${property.code_postal ?? ""}</p>
        <p><strong>Commune:</strong> ${property.nom_commune ?? ""}</p>
      </div>
    `)

    this.markers.push(marker)
  }

  // Bascule l'affichage de la table de propriétés
  toggleTable(): void {
    this.tableCollapsed = !this.tableCollapsed

    // Recalcul de la taille de la carte après animation
    setTimeout(() => {
      if (this.map) {
        this.map.invalidateSize()
      }
    }, 300)
  }

  // Sélection d'une propriété depuis la table
  selectProperty(index: number, property: DvfProperty): void {
    this.selectedPropertyIndex = index

    // Déplie la table si elle est repliée
    if (this.tableCollapsed) {
      this.tableCollapsed = false
    }

    // Centre la carte sur la propriété sélectionnée
    this.map.setView([property.latitude, property.longitude], 16)

    // Fait défiler la ligne sélectionnée dans la table
    setTimeout(() => {
      const selectedRow = document.querySelector(".property-table tr.selected")
      if (selectedRow) {
        selectedRow.scrollIntoView({ behavior: "smooth", block: "nearest" })
      }
    }, 100)
  }
}
