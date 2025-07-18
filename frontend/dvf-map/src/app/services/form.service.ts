import { Injectable, inject } from "@angular/core"
import { BehaviorSubject, type Observable } from "rxjs"

@Injectable({ providedIn: "root" }) // Le service est injecté globalement (singleton)
export class FormService {
  // Subject qui contient la plage de prix sélectionnée (ou null si aucun filtre actif)
  private priceFilterSubject = new BehaviorSubject<[number, number] | null>(null)

  // Subject qui contient la plage de dates sélectionnée (ou null si aucun filtre actif)
  private dateFilterSubject = new BehaviorSubject<[string, string] | null>(null)

  // Subject pour stocker les critères de recherche et déclencher la recherche
  private searchCriteriaSubject = new BehaviorSubject<any>(null)

  // Permet d'observer les changements du filtre de prix
  getPriceFilterObservable(): Observable<[number, number] | null> {
    return this.priceFilterSubject.asObservable()
  }

  // Permet d'observer les changements du filtre de date
  getDateFilterObservable(): Observable<[string, string] | null> {
    return this.dateFilterSubject.asObservable()
  }

  // NOUVEAU : Observable pour les critères de recherche
  getSearchCriteriaObservable(): Observable<any> {
    return this.searchCriteriaSubject.asObservable()
  }

  // Déclenche la mise à jour du filtre de prix (utilisé par le formulaire)
  setPriceFilter(minPrice: number, maxPrice: number): void {
    this.priceFilterSubject.next([minPrice, maxPrice])
  }

  // Déclenche la mise à jour du filtre de date (utilisé par le formulaire)
  setDateFilter(startDate: string, endDate: string): void {
    this.dateFilterSubject.next([startDate, endDate])
  }

  // Réinitialise le filtre de prix (utilisé lors du reset ou quand décoché)
  clearPriceFilter(): void {
    this.priceFilterSubject.next(null)
  }

  // Réinitialise le filtre de date
  clearDateFilter(): void {
    this.dateFilterSubject.next(null)
  }

  /**
   * NOUVELLE MÉTHODE SIMPLIFIÉE : Compatible avec votre système existant
   * Au lieu de faire l'appel API ici, on émet les critères pour que MapComponent les récupère
   */
  async searchProperties(searchCriteria: any): Promise<any[]> {
    try {
      console.log('🔍 FormService - Émission des critères de recherche:', searchCriteria)

      // Appliquer les filtres à votre système existant
      if (searchCriteria.price) {
        this.setPriceFilter(searchCriteria.price, searchCriteria.price)
      } else if (searchCriteria.minPrice && searchCriteria.maxPrice) {
        this.setPriceFilter(searchCriteria.minPrice, searchCriteria.maxPrice)
      }

      if (searchCriteria.date) {
        this.setDateFilter(searchCriteria.date, searchCriteria.date)
      } else if (searchCriteria.startDate && searchCriteria.endDate) {
        this.setDateFilter(searchCriteria.startDate, searchCriteria.endDate)
      }

      // Émettre les critères pour que MapComponent puisse les utiliser
      this.searchCriteriaSubject.next(searchCriteria)

      console.log('✅ FormService - Critères émis, MapComponent va traiter la recherche')

      // Retourner une promesse vide car MapComponent gère la recherche
      return Promise.resolve([])

    } catch (error) {
      console.error('❌ FormService - Erreur:', error)
      throw error
    }
  }
}
