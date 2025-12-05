from scrapfly import ScrapeConfig, ScrapflyClient, ScrapeApiResponse
from typing import Dict, List, Optional
import asyncio
import json
import requests
import time
import datetime
import os
from contextlib import suppress
from utils import WebScrapingPerformanceAnalyzer
from dotenv import load_dotenv
from db_config import DatabaseManager

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Clé API pour Scrapfly
KEY = os.getenv("SCRAPFLY_API_KEY", "scp-live-0a3cf57c20f14e4483bce86a12210a76")
if not KEY:
    raise ValueError("La clé API Scrapfly n'a pas été trouvée dans les variables d'environnement.")


def fetch_image(url: str) -> Optional[bytes]:
    """Télécharge une image depuis une URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image {url} : {str(e)}")
        return None

def save_data(incoming_data: Dict, analyzer: WebScrapingPerformanceAnalyzer) -> tuple[int, int]:
    """Sauvegarde les données dans un fichier JSON et les images dans des fichiers séparés"""
    output_dir = "scraped_data"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    image_paths = []
    image_urls = incoming_data.get('images', {}).get('urls', [])
    error_count = 0

    for i, url in enumerate(image_urls, start=1):
        image_data = fetch_image(url)
        if image_data:
            image_filename = f"{output_dir}/image_{timestamp}_{i}.jpeg"
            with open(image_filename, "wb") as img_file:
                img_file.write(image_data)
            image_paths.append(image_filename)
            print(f"Image {i} sauvegardée dans {image_filename}")
        else:
            image_paths.append(None)
            error_count += 1
            print(f"Échec du téléchargement de l'image {i} depuis {url}")

    incoming_data.pop('image_1', None)
    incoming_data['image_paths'] = image_paths

    json_filename = f"{output_dir}/data_{timestamp}.json"
    with open(json_filename, "w", encoding="utf-8") as json_file:
        json.dump(incoming_data, json_file, ensure_ascii=False, indent=4)

    print(f"Données sauvegardées dans {json_filename}")
    return error_count, len(image_urls)

def get_object_by_value(data: List[Dict], key: str, value: str) -> Optional[str]:
    """Récupère une valeur spécifique depuis une liste de dictionnaires"""
    with suppress(TypeError, KeyError):
        for item in data:
            if item.get(key) == value:
                return item.get('value_label')
    return None

# Initialisation du client Scrapfly
SCRAPFLY = ScrapflyClient(key=KEY)

# Configuration de base pour Scrapfly
BASE_CONFIG = {
    "asp": True,
    "country": "fr",
    "proxy_pool": "public_residential_pool"
}

def parse_search(result: ScrapeApiResponse) -> Optional[Dict]:
    """Parse les données de recherche depuis la réponse Scrapfly"""
    try:
        next_data = result.selector.css("script[id='__NEXT_DATA__']::text").get()
        if not next_data:
            return None
        ads_data = json.loads(next_data)
        for _ in range(3):  # 3 tentatives max
            if 'ad' in ads_data.get('props', {}).get('pageProps', {}):
                return ads_data['props']['pageProps']['ad']
            time.sleep(1)
        return None
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Erreur lors du parsing : {str(e)}")
        return None

async def scrape_search(url: str, max_pages: int, analyzer: WebScrapingPerformanceAnalyzer, db_manager: DatabaseManager) -> Optional[Dict]:
    """Effectue le scraping d'une URL et enregistre les données"""
    print(f"Scraping de la recherche {url}")
    start_time = time.time()
    request_count = 0
    error_count = 0
    data_points = 0
    proxy_attempts = 0
    response_size = 0

    try:
        request_count += 1
        proxy_attempts += 1  # Incrémentation pour la requête initiale
        first_page = await asyncio.wait_for(SCRAPFLY.async_scrape(ScrapeConfig(url, **BASE_CONFIG)), timeout=15)
        response_size = len(first_page.content)
        search_data = parse_search(first_page)

        if not search_data:
            raise ValueError("Aucune donnée d'annonce trouvée")

        # Structure des données de réponse
        response = {
            'adresse': search_data.get("location", {}).get("city_label", None),
            'title': search_data.get("subject", None),
            'prix': search_data.get("price_cents", 0)/100 if search_data.get("price_cents") else None,
            'type_habitat': get_object_by_value(search_data.get("attributes", []), "key", "real_estate_type"),
            'surface_habitable': get_object_by_value(search_data.get("attributes", []), "key", "square"),
            'surface_terrain': get_object_by_value(search_data.get("attributes", []), "key", "land_plot_surface"),
            'nbr_pieces': get_object_by_value(search_data.get("attributes", []), "key", "rooms"),
            'dpe': get_object_by_value(search_data.get("attributes", []), "key", "energy_rate"),
            'ges': get_object_by_value(search_data.get("attributes", []), "key", "ges"),
            'description': search_data.get("body", None),
            'images': {"urls": search_data.get('images', {}).get('urls', [])},
            'image_1': fetch_image(search_data.get('images', {}).get('urls', [None])[0]) if search_data.get('images', {}).get('urls') else None,
            "html_content": first_page.content
        }

        img_error_count, img_count = save_data(response, analyzer)
        error_count += img_error_count
        data_points = sum(1 for v in response.values() if v is not None) + img_count

        # Enregistrement dans la base de données
        db_manager.save_to_db(response)

        execution_time = time.time() - start_time
        analyzer.log_performance(execution_time, request_count, response_size, proxy_attempts)

        return response
    except (asyncio.TimeoutError, ValueError, Exception) as e:
        error_count += 1
        execution_time = time.time() - start_time
        analyzer.log_performance(execution_time, request_count, response_size, proxy_attempts)
        print(f"Erreur lors du scraping : {str(e)}")
        return None
