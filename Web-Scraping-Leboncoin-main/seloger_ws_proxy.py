import asyncio
import json
import os
import datetime
import time
import requests
import sys
import uuid
from typing import Dict, Optional, List
from contextlib import suppress
import psycopg2
from psycopg2 import Error
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.async_api import async_playwright

# Configuration Bright Data
customer_id = "hl_d2d90740"
zone = "residential_proxy1"
password = "6rdsqopy5yrg"
proxy_host = "brd.superproxy.io"
proxy_port = 33335
proxy = f"http://brd-customer-{customer_id}-zone-{zone}:{password}@{proxy_host}:{proxy_port}"

# Configuration Bright Data pour le navigateur
BROWSER_AUTH = 'brd-customer-hl_d2d90740-zone-scraping_browser1:x86w4rrdc83a'
SBR_WS_CDP = f'wss://{BROWSER_AUTH}@brd.superproxy.io:9222'

class WebScrapingPerformanceAnalyzer:
    """Classe pour analyser et visualiser les performances du scraping."""
    def __init__(self):
        self.performance_data = {
            'timestamps': [],
            'execution_times': [],
            'request_counts': [],
            'response_sizes': [],
            'proxy_attempts': []
        }
    
    def log_performance(self, execution_time: float, request_count: int, 
                       response_size: int, proxy_attempts: int):
        self.performance_data['timestamps'].append(datetime.datetime.now())
        self.performance_data['execution_times'].append(execution_time)
        self.performance_data['request_counts'].append(request_count)
        self.performance_data['response_sizes'].append(response_size)
        self.performance_data['proxy_attempts'].append(proxy_attempts)
    
    def plot_performance_metrics(self, output_file: str = "seloger_performance.png") -> str:
        df = pd.DataFrame(self.performance_data)
        if df.empty:
            return "Aucune donnée pour générer les graphiques"
        
        plt.figure(figsize=(15, 10))
        
        plt.subplot(3, 1, 1)
        plt.plot(df['request_counts'], df['execution_times'], 'b-', marker='o')
        plt.title('Temps d\'exécution vs Nombre de requêtes')
        plt.xlabel('Nombre de requêtes')
        plt.ylabel('Temps d\'exécution (secondes)')
        plt.grid(True)
        
        plt.subplot(3, 1, 2)
        plt.hist(df['response_sizes'], bins=20, color='g', edgecolor='black')
        plt.title('Distribution du volume de données par requête')
        plt.xlabel('Taille de la réponse (octets)')
        plt.ylabel('Fréquence')
        plt.grid(True, alpha=0.3)
        
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
    """Classe pour gérer la connexion et les opérations avec la base de données PostgreSQL."""
    def __init__(self):
        self.conn_params = {
            "host": "localhost",
            "port": "5432",
            "database": "auth_db",
            "user": "brayanne",
            "password": "brayanne"
        }
        self.conn = None
        self.create_table()

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            return True
        except Error as e:
            print(f"Erreur de connexion à la base de données : {e}")
            return False

    def create_table(self):
        try:
            if self.connect():
                with self.conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS Annonces (
                            id VARCHAR(36) PRIMARY KEY,
                            adresse TEXT,
                            titre TEXT,
                            prix TEXT,
                            type_habitat TEXT,
                            surface_habitable TEXT,
                            surface_terrain TEXT,
                            nbr_pieces TEXT,
                            dpe TEXT,
                            ges TEXT,
                            description TEXT,
                            image_paths TEXT[],
                            reference TEXT,
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
        try:
            if self.connect():
                with self.conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO Annonces (
                            id, adresse, titre, prix, type_habitat, surface_habitable,
                            surface_terrain, nbr_pieces, dpe, ges, description, image_paths, reference
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data.get('id'),
                        data.get('adresse'),
                        data.get('titre'),
                        data.get('prix'),
                        data.get('type_habitat'),
                        data.get('surface_habitable'),
                        data.get('surface_terrain'),
                        data.get('nbr_pieces'),
                        data.get('dpe'),
                        data.get('ges'),
                        data.get('description'),
                        data.get('image_paths', []),
                        data.get('reference')
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
    try:
        response = requests.get(url, proxies={"http": proxy, "https": proxy}, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image {url} : {e}")
        return None

def save_data(incoming_data: Dict, analyzer: WebScrapingPerformanceAnalyzer) -> tuple[int, int]:
    output_dir = "scraped_data_seloger"
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

    incoming_data['image_paths'] = image_paths
    json_filename = f"{output_dir}/data_{timestamp}.json"
    with open(json_filename, "w", encoding="utf-8") as json_file:
        json.dump(incoming_data, json_file, ensure_ascii=False, indent=4)

    print(f"Données sauvegardées dans {json_filename}")
    return error_count, len(image_urls)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def scrape_with_retry(url: str) -> str:
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(SBR_WS_CDP)
        try:
            page = await browser.new_page()
            await page.goto(url, timeout=60000)
            await page.wait_for_load_state('networkidle')
            content = await page.content()
            response_size = len(content.encode('utf-8'))
            await page.close()
            return content, response_size
        finally:
            await browser.close()

def parse_search(content: str) -> Optional[Dict]:
    try:
        soup = BeautifulSoup(content, "html.parser")
        
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Contenu HTML sauvegardé dans debug.html")
        
        main_features_div = soup.find("div", string=re.compile(r"\d+ pièces.*\d+ m²"))
        print(f"main_features_div: {main_features_div}")
        main_features = main_features_div.text.split("•") if main_features_div else []
        
        characteristics_div = soup.find("div", string="Caractéristiques")
        print(f"characteristics_div: {characteristics_div}")
        characteristics = [li.text.strip() for li in characteristics_div.find_next("ul").find_all("li")] if characteristics_div else []
        
        image_elements = soup.select("div img")
        print(f"image_elements: {len(image_elements)} found")
        image_urls = [img.get("src") for img in image_elements if img.get("src")]

        scale_elements = soup.select("div.css-r92wp3 div[data-testid='cdp-preview-scale-highlighted']")
        print(f"scale_elements found: {len(scale_elements)}")
        dpe_scale = scale_elements[0] if len(scale_elements) > 0 else None
        ges_scale = scale_elements[1] if len(scale_elements) > 1 else None
        
        if not dpe_scale:
            dpe_div = soup.find("div", string="Diagnostic de performance énergétique (DPE)")
            dpe_scale = dpe_div.find_next("div") if dpe_div else None
        if not ges_scale:
            ges_div = soup.find("div", string="Indice d'émission de gaz à effet de serre (GES)")
            ges_scale = ges_div.find_next("div") if ges_div else None
        
        print(f"dpe_scale: {dpe_scale}")
        print(f"ges_scale: {ges_scale}")

        type_element = soup.select_one("span.css-1b9ytm[data-testid='cdp-hardfacts']") or \
                       soup.find(lambda tag: tag.name in ["span", "div", "h2"] and \
                                 re.search(r".*à vendre", tag.text, re.IGNORECASE))
        print(f"type_element: {type_element}")
        type_habitat = None
        if type_element:
            type_text = type_element.text.strip()
            type_habitat = re.sub(r"à vendre", "", type_text, flags=re.IGNORECASE).strip()

        id_div = soup.find("div", string=re.compile("Identifiant:"))
        print(f"id_div: {id_div}")
        adresse_div = soup.find("div", string=re.compile(r".*, \w+ \d+.*\(\d+\)"))
        print(f"adresse_div: {adresse_div}")
        titre_div = soup.find("h2") or soup.find("div", string=re.compile(r"À VENDRE.*"))
        print(f"titre_div: {titre_div}")
        prix_span = soup.select_one("span.css-otf0vo")
        print(f"prix_span: {prix_span}")
        ref_div = soup.find("div", string=re.compile("Référence annonce:"))
        print(f"ref_div: {ref_div}")

        return {
            "id": id_div.text.replace("Identifiant:", "").strip() if id_div else str(uuid.uuid4()),
            "adresse": adresse_div.text.strip() if adresse_div else None,
            "titre": titre_div.text.strip() if titre_div else None,
            "prix": prix_span.text.strip() if prix_span else None,
            "type_habitat": type_habitat,
            "surface_habitable": next((f.strip() for f in main_features if "m²" in f and "terrain" not in f), None),
            "surface_terrain": next((c for c in characteristics if "m² de terrain" in c), None),
            "nbr_pieces": next((f.strip() for f in main_features if "pièces" in f), None),
            "dpe": dpe_scale.text.strip() if dpe_scale else None,
            "ges": ges_scale.text.strip() if ges_scale else None,
            "description": titre_div.find_parent().text.strip() if titre_div and titre_div.find_parent() else None,
            "images": {"urls": image_urls},
            "reference": ref_div.text.replace("Référence annonce:", "").strip() if ref_div else None
        }
    except (AttributeError, Exception) as e:
        print(f"Erreur détaillée lors du parsing : {e}")
        return None

async def scrape_search(url: str, max_pages: int, analyzer: WebScrapingPerformanceAnalyzer, db_manager: DatabaseManager) -> Optional[Dict]:
    print(f"Scraping de l'annonce {url}")
    start_time = time.time()
    request_count = 0
    error_count = 0
    proxy_attempts = 0
    response_size = 0
    
    try:
        request_count += 1
        proxy_attempts += 1
        content, response_size = await scrape_with_retry(url)
        search_data = parse_search(content)
        
        if not search_data:
            raise ValueError("Aucune donnée d'annonce trouvée")
        
        img_error_count, img_count = save_data(search_data, analyzer)
        error_count += img_error_count
        
        db_manager.save_to_db(search_data)
        
        execution_time = time.time() - start_time
        analyzer.log_performance(execution_time, request_count, response_size, proxy_attempts)
        
        return search_data
    except (asyncio.TimeoutError, ValueError, Exception) as e:
        error_count += 1
        execution_time = time.time() - start_time
        analyzer.log_performance(execution_time, request_count, response_size, proxy_attempts)
        print(f"Erreur lors du scraping : {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erreur : Veuillez fournir une URL d'annonce SeLoger en argument.")
        print("Exemple : python ws_slg_brightdata.py https://www.seloger.com/annonces/achat/maison/marseille-12eme-13/saint-julien/243477581.htm")
        sys.exit(1)
    
    analyzer = WebScrapingPerformanceAnalyzer()
    db_manager = DatabaseManager()
    
    try:
        url = sys.argv[1]
        response = asyncio.run(scrape_search(url=url, max_pages=1, analyzer=analyzer, db_manager=db_manager))
        
        if response is not None:
            print("Scraping réussi")
            print(json.dumps(response, indent=4, ensure_ascii=False))
        else:
            print("Échec du scraping")
            
        print(analyzer.plot_performance_metrics())
    except Exception as e:
        print(f"Erreur inattendue : {e}")
        sys.exit(1)
