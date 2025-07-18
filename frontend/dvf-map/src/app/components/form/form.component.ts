import { Component, inject, type OnInit } from "@angular/core"
import { FormBuilder, type FormGroup, ReactiveFormsModule } from "@angular/forms"
import { CommonModule } from "@angular/common"

// Importation des services personnalisés
import { FormService } from "../../services/form.service"
import { MapService } from "../../services/map.service"
import { AppComponent } from "../../app.component"

@Component({
  selector: "app-form",
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: "./form.component.html",
  styleUrls: ["./form.component.scss"],
})
export class FormComponent implements OnInit {
  // Formulaire réactif
  filterForm: FormGroup

  // État du composant
  isLoading = false

  // Injection de dépendances
  private readonly fb = inject(FormBuilder)
  private readonly formService = inject(FormService)
  private readonly mapService = inject(MapService)
  private readonly appComponent = inject(AppComponent)

  constructor() {
    // Initialisation du formulaire
    this.filterForm = this.fb.group({
      // Filtres de prix
      usePriceFilter: [false],
      priceMode: ["interval"],
      price: [null],
      minPrice: [null],
      maxPrice: [null],

      // Filtres de date
      useDateFilter: [false],
      dateMode: ["interval"],
      exactDate: [null],
      startDate: [null],
      endDate: [null],
    })
  }

  ngOnInit(): void {
    // Observation de l'état du filtre de prix
    this.filterForm.get("usePriceFilter")?.valueChanges.subscribe((enabled: boolean) => {
      if (!enabled) {
        this.formService.clearPriceFilter()
        this.mapService.refreshMap()
      }
    })

    // Observation de l'état du filtre de date
    this.filterForm.get("useDateFilter")?.valueChanges.subscribe((enabled: boolean) => {
      if (!enabled) {
        this.formService.clearDateFilter()
        this.mapService.refreshMap()
      }
    })
  }

  /**
   * Vérifier si au moins un filtre est activé
   */
  hasActiveFilters(): boolean {
    const formValue = this.filterForm.value
    return formValue.usePriceFilter || formValue.useDateFilter
  }

  /**
   * Méthode de recherche SIMPLIFIÉE - Compatible avec votre système existant
   */
  search(): void {
    if (!this.hasActiveFilters() || this.isLoading) {
      return
    }

    this.isLoading = true
    const values = this.filterForm.value

    // Gestion du filtre de prix
    if (values.usePriceFilter) {
      if (values.priceMode === "exact") {
        const val = Number(values.price)
        this.formService.setPriceFilter(val, val)
      } else {
        const min = Number(values.minPrice)
        const max = Number(values.maxPrice)
        this.formService.setPriceFilter(min, max)
      }
    } else {
      this.formService.clearPriceFilter()
    }

    // Gestion du filtre de date
    if (values.useDateFilter) {
      if (values.dateMode === "exact") {
        const date = values.exactDate
        this.formService.setDateFilter(date, date)
      } else {
        const start = values.startDate
        const end = values.endDate || start // Si endDate est vide, on prend start
        this.formService.setDateFilter(start, end)
      }
    } else {
      this.formService.clearDateFilter()
    }

    // Déclencher le rafraîchissement de la carte
    this.mapService.refreshMap()

    // Fermer la sidebar sur mobile
    if (window.innerWidth <= 768) {
      this.appComponent.sidebarOpen = false
    }

    // Simuler un petit délai pour l'état de chargement
    setTimeout(() => {
      this.isLoading = false
    }, 500)

    console.log('✅ Recherche effectuée via le système existant')
  }

  /**
   * Réinitialiser les filtres
   */
  resetFilters(): void {
    this.filterForm.patchValue({
      usePriceFilter: false,
      priceMode: "interval",
      price: null,
      minPrice: null,
      maxPrice: null,

      useDateFilter: false,
      dateMode: "interval",
      exactDate: null,
      startDate: null,
      endDate: null,
    })

    this.formService.clearPriceFilter()
    this.formService.clearDateFilter()

    this.mapService.refreshMap()
  }
}
