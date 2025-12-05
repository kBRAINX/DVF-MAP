import asyncio
import sys
from config import init_db, WebScrapingPerformanceAnalyzer
from lbc_ws_proxy_methods import scrape_search


# Fichier principal du script de scraping avec Bright Data
if __name__ == "__main__":
    init_db()  # Initialiser la base de données au démarrage
    analyzer = WebScrapingPerformanceAnalyzer()

    try:
        url = sys.argv[1]
        response = asyncio.run(scrape_search(url=url, analyzer=analyzer))

        if response is not None:
            print("Scraping réussi")
        else:
            print("Échec du scraping")

        print(analyzer.plot_performance_metrics())
    except IndexError:
        print("Erreur: Veuillez fournir une URL en argument")
    except Exception as e:
        print(f"Erreur inattendue: {str(e)}")
