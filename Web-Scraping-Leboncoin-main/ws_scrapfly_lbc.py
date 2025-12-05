import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scrapfly import ScrapeConfig, ScrapflyClient, ScrapeApiResponse
from typing import Dict, List, Optional
import asyncio
import json
import sys
import requests
import time
import datetime
import os
from contextlib import suppress
import psycopg2
from psycopg2 import Error

# Clé API pour Scrapfly
KEY = "scp-live-0a3cf57c20f14e4483bce86a12210a76"

class WebScrapingPerformanceAnalyzer:
    def __init__(self):
        # Initialisation des métriques de performance
        self.performance_data = {
            'timestamps': [],          # Horodatages des sessions
            'execution_times': [],     # Temps d'exécution
            'request_counts': [],      # Nombre de requêtes
            'response_sizes': [],      # Taille des réponses
            'proxy_attempts': []       # Tentatives de proxy
        }
    
    def log_performance(self, execution_time: float, request_count: int, 
                       response_size: int, proxy_attempts: int):
        """Enregistre les métriques de performance pour une session de scraping"""
        self.performance_data['timestamps'].append(datetime.datetime.now())
        self.performance_data['execution_times'].append(execution_time)
        self.performance_data['request_counts'].append(request_count)
        self.performance_data['response_sizes'].append(response_size)
        self.performance_data['proxy_attempts'].append(proxy_attempts)
    
    def plot_performance_metrics(self, output_file: str = "performance_analysis.png") -> str:
        """Génère et sauvegarde les graphiques d'analyse de performance"""
        df = pd.DataFrame(self.performance_data)
        if df.empty:
            return "Aucune donnée pour générer les graphiques"
        
        plt.figure(figsize=(15, 10))
        
        # Graphique 1 : Temps d'exécution vs nombre de requêtes
        plt.subplot(3, 1, 1)
        plt.plot(df['request_counts'], df['execution_times'], 'b-', marker='o')
        plt.title('Temps d\'exécution vs Nombre de requêtes')
        plt.xlabel('Nombre de requêtes')
        plt.ylabel('Temps d\'exécution (secondes)')
        plt.grid(True)
        
        # Graphique 2 : Histogramme du volume de données
        plt.subplot(3, 1, 2)
        plt.hist(df['response_sizes'], bins=20, color='g', edgecolor='black')
        plt.title('Distribution du volume de données par requête')
        plt.xlabel('Taille de la réponse (octets)')
        plt.ylabel('Fréquence')
        plt.grid(True, alpha=0.3)
        
        # Graphique 3 : Tentatives de proxy vs nombre de requêtes
        plt.subplot(3, 1, 3)
        plt.plot(df['request_counts'], df['proxy_attempts'], 'r-', marker='o')
        plt.title('Tentatives de proxy vs Nombre de requêtes')
        plt.xlabel('Nombre de requêtes')
        plt.ylabel('Tentatives de proxy')
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        
        return f"Graphiques de performance sauvegardés dans {output_file}"

class DatabaseManager:
    def __init__(self):
        # Paramètres de connexion à la base de données
        self.conn_params = {
            "host": "localhost",
            "port": "5432",
            "database": "immo_bd",
            "user": "admin",
            "password": "Nuttertools237"
        }
        self.conn = None
        self.create_table()

    def connect(self):
        """Établit la connexion à la base de données PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            return True
        except Error as e:
            print(f"Erreur de connexion à la base de données : {e}")
            return False

    def create_table(self):
        """Crée la table Annonces si elle n'existe pas"""
        try:
            if self.connect():
                with self.conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS Annonces (
                            id SERIAL PRIMARY KEY,
                            adresse TEXT,
                            title TEXT,
                            prix FLOAT,
                            type_habitat TEXT,
                            surface_habitable TEXT,
                            surface_terrain TEXT,
                            nbr_pieces TEXT,
                            dpe TEXT,
                            ges TEXT,
                            description TEXT,
                            image_paths TEXT[],
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    self.conn.commit()
        except Error as e:
            print(f"Erreur lors de la création de la table : {e}")
        finally:
            if self.conn:
                self.conn.close()

    def save_to_db(self, data: Dict) -> bool:
        """Enregistre les données dans la table Annonces"""
        try:
            if self.connect():
                with self.conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO Annonces (
                            adresse, title, prix, type_habitat, surface_habitable,
                            surface_terrain, nbr_pieces, dpe, ges, description, image_paths
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data.get('adresse'),
                        data.get('title'),
                        data.get('prix'),
                        data.get('type_habitat'),
                        data.get('surface_habitable'),
                        data.get('surface_terrain'),
                        data.get('nbr_pieces'),
                        data.get('dpe'),
                        data.get('ges'),
                        data.get('description'),
                        data.get('image_paths')
                    ))
                    self.conn.commit()
                return True
        except Error as e:
            print(f"Erreur lors de l'enregistrement dans la base de données : {e}")
            return False
        finally:
            if self.conn:
                self.conn.close()
        return False

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