import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import urllib.request
import ssl
import psycopg2
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, List, Optional
import asyncio
import json
import sys
import time
import datetime
import os
from contextlib import suppress

# Configuration Bright Data pour les proxies HTTP (pour les images uniquement)
customer_id = "hl_341de7f4"
zone = "residential_proxy1"
password = "b0q6na4fz3nz"
proxy_host = "brd.superproxy.io"
proxy_port = 33335
proxy = f"http://brd-customer-{customer_id}-zone-{zone}:{password}@{proxy_host}:{proxy_port}"

# Configuration Bright Data pour le navigateur
BROWSER_AUTH = 'brd-customer-hl_341de7f4-zone-scraping_browser1:mp3rf2c5h2k8'
SBR_WS_CDP = f'wss://{BROWSER_AUTH}@brd.superproxy.io:9222'

# Configuration de la base de données PostgreSQL
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "immo_bd",
    "user": "admin",
    "password": "Nuttertools237"
}

class WebScrapingPerformanceAnalyzer:
    def __init__(self):
        self.performance_data = {
            'timestamps': [],
            'execution_times': [],
            'request_counts': [],
            'error_counts': [],
            'data_points': [],
            'success_rates': [],
            'response_sizes': [],
            'screenshot_success': [],
            'proxy_counts': [],  # Nombre de proxies utilisés (fixe à 1 pour Bright Data)
            'node_counts': []    # Nombre de nœuds parcourus (requêtes réseau)
        }
    
    def log_performance(self, execution_time: float, request_count: int, 
                       error_count: int, data_points: int, 
                       success_rate: float, response_size: int,
                       screenshot_success: bool, proxy_count: int, node_count: int):
        """Enregistre les métriques de performance pour une session de scraping"""
        self.performance_data['timestamps'].append(datetime.datetime.now())
        self.performance_data['execution_times'].append(execution_time)
        self.performance_data['request_counts'].append(request_count)
        self.performance_data['error_counts'].append(error_count)
        self.performance_data['data_points'].append(data_points)
        self.performance_data['success_rates'].append(success_rate)
        self.performance_data['response_sizes'].append(response_size)
        self.performance_data['screenshot_success'].append(screenshot_success)
        self.performance_data['proxy_counts'].append(proxy_count)
        self.performance_data['node_counts'].append(node_count)
    
    def plot_performance_metrics(self, output_file: str = "performance_analysis.png") -> str:
        """Génère et sauvegarde des graphiques d'analyse des performances"""
        df = pd.DataFrame(self.performance_data)
        if df.empty:
            return "Aucune donnée pour générer les graphiques"
        
        plt.figure(figsize=(15, 15))
        
        # Graphique 1 : Temps d'exécution en fonction du nombre de requêtes
        plt.subplot(3, 1, 1)
        plt.scatter(df['request_counts'], df['execution_times'], color='b', marker='o')
        plt.title('Temps d\'exécution en fonction du nombre de requêtes')
        plt.xlabel('Nombre de requêtes')
        plt.ylabel('Temps (secondes)')
        plt.grid(True)
        
        # Graphique 2 : Volume des données échangées en fonction du nombre de requêtes
        plt.subplot(3, 1, 2)
        plt.scatter(df['request_counts'], df['response_sizes'], color='g', marker='o')
        plt.title('Volume des données échangées en fonction du nombre de requêtes')
        plt.xlabel('Nombre de requêtes')
        plt.ylabel('Taille des réponses (octets)')
        plt.grid(True)
        
        # Graphique 3 : Nombre de proxies et nœuds parcourus en fonction du nombre de requêtes
        plt.subplot(3, 1, 3)
        plt.plot(df['request_counts'], df['proxy_counts'], 'r-', marker='o', label='Proxies (fixe)')
        plt.plot(df['request_counts'], df['node_counts'], 'm-', marker='s', label='Nœuds parcourus')
        plt.title('Proxies et nœuds parcourus en fonction du nombre de requêtes')
        plt.xlabel('Nombre de requêtes')
        plt.ylabel('Nombre')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()
        
        return f"Graphiques de performance sauvegardés dans {output_file}"

def init_db():
    """Initialise la table Annonces dans la base de données immo_db."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        create_table_query = """
        CREATE TABLE IF NOT EXISTS Annonces (
            id SERIAL PRIMARY KEY,
            url VARCHAR(500),
            adresse VARCHAR(255),
            title VARCHAR(255),
            prix FLOAT,
            type_habitat VARCHAR(100),
            surface_habitable VARCHAR(50),
            surface_terrain VARCHAR(50),
            nbr_pieces VARCHAR(50),
            dpe VARCHAR(50),
            ges VARCHAR(50),
            description TEXT,
            image_paths TEXT[],  -- Tableau de chaînes pour les chemins des images
            screenshot_path VARCHAR(255),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(create_table_query)
        conn.commit()
        print("Table Annonces créée ou déjà existante")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
    finally:
        cursor.close()
        conn.close()

def save_to_db(data: Dict, url: str, image_paths: List[Optional[str]], screenshot_path: str):
    """Sauvegarde les données pertinentes dans la base de données immo_db."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        insert_query = """
        INSERT INTO Annonces (
            url, adresse, title, prix, type_habitat, surface_habitable, 
            surface_terrain, nbr_pieces, dpe, ges, description, image_paths, 
            screenshot_path, timestamp
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        image_paths = [path for path in image_paths if path is not None]  # Filtrer les chemins nuls
        cursor.execute(insert_query, (
            url,
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
            image_paths,
            screenshot_path,
            datetime.datetime.now()
        ))
        conn.commit()
        print("Données sauvegardées dans la base de données")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde dans la base de données : {str(e)}")
    finally:
        cursor.close()
        conn.close()

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((urllib.error.URLError, urllib.error.HTTPError))
)
def fetch_image(url: str) -> Optional[bytes]:
    """Télécharge une image en utilisant urllib.request avec le proxy résidentiel."""
    try:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({'https': proxy, 'http': proxy}),
            urllib.request.HTTPSHandler(context=ssl._create_unverified_context())
        )
        opener.addheaders = [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'),
            ('Accept', 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'),
            ('Accept-Language', 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'),
            ('Accept-Encoding', 'gzip, deflate, br'),
            ('Connection', 'keep-alive'),
            ('Referer', 'https://www.leboncoin.fr/')
        ]
        response = opener.open(url, timeout=10)
        if response.getcode() == 200:
            print(f"Image téléchargée avec succès depuis {url} (Statut: {response.getcode()})")
            return response.read()
        else:
            print(f"Échec du téléchargement de l'image depuis {url} (Statut: {response.getcode()})")
            return None
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"Erreur lors du téléchargement de l'image {url}: {str(e)}")
        return None
    except Exception as e:
        print(f"Erreur inattendue lors du téléchargement de l'image {url}: {str(e)}")
        return None

def save_data(incoming_data: Dict, analyzer: WebScrapingPerformanceAnalyzer, screenshot_success: bool, url: str, timestamp: str) -> tuple[int, int, List[Optional[str]], str]:
    """Sauvegarde les données dans un fichier JSON, les images dans un sous-dossier, et dans la base de données."""
    output_dir = "scraped_data"
    request_dir = f"{output_dir}/{timestamp}"
    os.makedirs(request_dir, exist_ok=True)

    image_paths = []
    image_urls = incoming_data.get('images', {}).get('urls', [])
    error_count = 0
    
    for i, url in enumerate(image_urls, start=1):
        try:
            image_data = fetch_image(url)
            if image_data:
                image_filename = f"{request_dir}/image_{timestamp}_{i}.jpeg"
                with open(image_filename, "wb") as img_file:
                    img_file.write(image_data)
                image_paths.append(image_filename)
                print(f"Image {i} sauvegardée dans {image_filename}")
            else:
                image_paths.append(None)
                error_count += 1
                print(f"Échec du téléchargement de l'image {i} depuis {url}")
            time.sleep(1)  # Délai pour éviter les blocages
        except Exception as e:
            image_paths.append(None)
            error_count += 1
            print(f"Échec du téléchargement de l'image {i} depuis {url}: {str(e)}")

    incoming_data.pop('image_1', None)
    incoming_data['image_paths'] = image_paths
    incoming_data['screenshot_success'] = screenshot_success

    json_filename = f"{request_dir}/data_{timestamp}.json"
    with open(json_filename, "w", encoding="utf-8") as json_file:
        json.dump(incoming_data, json_file, ensure_ascii=False, indent=4)

    screenshot_path = f"{request_dir}/screenshot_{timestamp}.png"
    save_to_db(incoming_data, url, image_paths, screenshot_path)

    print(f"Données sauvegardées dans {json_filename}")
    return error_count, len(image_urls), image_paths, screenshot_path

def get_object_by_value(data: List[Dict], key: str, value: str) -> Optional[str]:
    with suppress(TypeError, KeyError):
        for item in data:
            if item.get(key) == value:
                return item.get('value_label')
    return None

def parse_search(html_content: str) -> Optional[Dict]:
    try:
        start_marker = '<script id="__NEXT_DATA__" type="application/json">'
        end_marker = '</script>'
        start_idx = html_content.find(start_marker) + len(start_marker)
        end_idx = html_content.find(end_marker, start_idx)
        if start_idx == -1 or end_idx == -1:
            return None
            
        next_data = html_content[start_idx:end_idx]
        ads_data = json.loads(next_data)
        
        for _ in range(3):
            if 'ad' in ads_data.get('props', {}).get('pageProps', {}):
                return ads_data['props']['pageProps']['ad']
            time.sleep(1)
        return None
    except (json.JSONDecodeError, AttributeError) as e:
        print(f"Erreur lors du parsing: {str(e)}")
        return None

async def scrape_search(url: str, analyzer: WebScrapingPerformanceAnalyzer) -> Optional[Dict]:
    print(f"Scraping de {url}")
    start_time = time.time()
    request_count = 0
    error_count = 0
    data_points = 0
    response_size = 0
    screenshot_success = False
    node_count = 0  # Compteur pour les nœuds parcourus (requêtes réseau)
    
    output_dir = "scraped_data"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    request_dir = f"{output_dir}/{timestamp}"
    os.makedirs(request_dir, exist_ok=True)
    
    async with async_playwright() as pw:
        for attempt in range(3):
            try:
                print(f'Connexion à l\'API du navigateur (Tentative {attempt + 1}/3)...')
                browser = await pw.chromium.connect_over_cdp(SBR_WS_CDP)
                try:
                    page = await browser.new_page()
                    print('Connexion réussie ! Navigation vers la page')

                    # Compter les requêtes réseau pour estimer les nœuds parcourus
                    def handle_request(request):
                        nonlocal node_count
                        node_count += 1
                    page.on("request", handle_request)

                    await page.goto(url, timeout=90000, wait_until="domcontentloaded")
                    request_count += 1
                    
                    # Accepter les cookies
                    try:
                        cookie_selectors = [
                            'button:contains("Accepter")',
                            'button:contains("Tout accepter")',
                            'button:contains("Accept")',
                            'button.axeptio_btn_accept',
                            'button[class*="accept"]',
                            '#didomi-notice-agree-button',
                            '[data-testid="accept-cookies"]'
                        ]
                        for selector in cookie_selectors:
                            try:
                                await page.wait_for_selector(selector, timeout=5000)
                                await page.click(selector)
                                print(f"Cookies acceptés avec le sélecteur: {selector}")
                                break
                            except PlaywrightTimeoutError:
                                continue
                        else:
                            print("Aucun bouton de cookies trouvé, poursuite du scraping")
                    except Exception as e:
                        print(f"Erreur lors de l'acceptation des cookies: {str(e)}")
                        error_count += 1
                    
                    # Attendre le script __NEXT_DATA__
                    try:
                        await page.wait_for_selector('script#__NEXT_DATA__', timeout=10000)
                        print("Script __NEXT_DATA__ détecté")
                    except PlaywrightTimeoutError:
                        print("Script __NEXT_DATA__ non détecté, tentative de poursuite")
                        error_count += 1
                    
                    await page.wait_for_timeout(2000)
                    
                    # Prendre la capture d'écran
                    screenshot_path = f"{request_dir}/screenshot_{timestamp}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"Capture d'écran sauvegardée dans '{screenshot_path}'")
                    screenshot_success = True
                    
                    # Récupérer le contenu HTML
                    html_content = await page.content()
                    search_data = parse_search(html_content)
                    
                    if not search_data:
                        raise ValueError("Aucune donnée d'annonce trouvée")
                    
                    response_data = {
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
                        "html_content": html_content
                    }
                    
                    response_size = len(html_content)
                    img_error_count, img_count, image_paths, screenshot_path = save_data(response_data, analyzer, screenshot_success, url, timestamp)
                    error_count += img_error_count
                    data_points = sum(1 for v in response_data.values() if v is not None) + img_count
                    success_rate = ((request_count - error_count) / request_count * 100) if request_count > 0 else 0
                    
                    execution_time = time.time() - start_time
                    proxy_count = 1  # Un seul proxy Bright Data utilisé par requête
                    analyzer.log_performance(execution_time, request_count, error_count, 
                                           data_points, success_rate, response_size, 
                                           screenshot_success, proxy_count, node_count)
                    
                    return response_data
                finally:
                    await browser.close()
            except PlaywrightTimeoutError as e:
                print(f"Timeout lors de la navigation (tentative {attempt + 1}/3): {str(e)}")
                error_count += 1
                if attempt == 2:
                    execution_time = time.time() - start_time
                    success_rate = ((request_count - error_count) / request_count * 100) if request_count > 0 else 0
                    analyzer.log_performance(execution_time, request_count, error_count, 
                                           data_points, success_rate, response_size, 
                                           screenshot_success, proxy_count=1, node_count=0)
                    print(f"Erreur lors du scraping: {str(e)}")
                    return None
            except Exception as e:
                print(f"Erreur lors de la navigation (tentative {attempt + 1}/3): {str(e)}")
                error_count += 1
                if attempt == 2:
                    execution_time = time.time() - start_time
                    success_rate = ((request_count - error_count) / request_count * 100) if request_count > 0 else 0
                    analyzer.log_performance(execution_time, request_count, error_count, 
                                           data_points, success_rate, response_size, 
                                           screenshot_success, proxy_count=1, node_count=0)
                    print(f"Erreur lors du scraping: {str(e)}")
                    return None
                await asyncio.sleep(5)

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