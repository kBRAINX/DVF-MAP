import asyncio
import sys
from utils import WebScrapingPerformanceAnalyzer
from db_config import DatabaseManager
from ws_scrapfly_lbc_methods import scrape_search

if __name__ == "__main__":
    # Initialisation des gestionnaires
    analyzer = WebScrapingPerformanceAnalyzer()
    db_manager = DatabaseManager()

    try:
        url = sys.argv[1]
        response = asyncio.run(scrape_search(url=url, max_pages=1, analyzer=analyzer, db_manager=db_manager))

        if response is not None:
            print("Scraping réussi")
        else:
            print("Échec du scraping")

        print(analyzer.plot_performance_metrics())
    except IndexError:
        print("Erreur : Veuillez fournir une URL en argument")
    except Exception as e:
        print(f"Erreur inattendue : {str(e)}")
