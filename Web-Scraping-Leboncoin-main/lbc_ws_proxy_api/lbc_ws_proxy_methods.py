import urllib.request
import ssl
import urllib.error
import psycopg2
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Dict, List, Optional
import asyncio
import json
import time
import datetime
import os
from contextlib import suppress
from config import *
import re


#Fonction pour la conversion des surfaces en entier
def extract_number(value: str) -> Optional[int]:
    """Extrait un entier depuis une chaîne comme '45 m²' → 45"""
    if isinstance(value, str):
        match = re.search(r'\d+', value.replace('\xa0', ' '))
        if match:
            return int(match.group())
    return None


# Fonction pour mettre à jour une annonce existante dans la base de données
# Paramètres :
#   - bien_id (int) : identifiant du bien immobilier à mettre à jour
#   - user_id (int) : identifiant de l'utilisateur propriétaire
#   - data (Dict) : dictionnaire contenant les détails de l’annonce (adresse, titre, prix, etc.)
#   - url (str) : lien source de l’annonce
#   - image_paths (List[Optional[str]]) : liste des chemins vers les images associées
#   - screenshot_path (str) : chemin vers la capture d’écran de l’annonce
# Comportement :
#   - Vérifie que l’annonce avec cet id et user_id existe
#   - Met à jour uniquement les champs autorisés
#   - Affiche un message d’erreur si la combinaison id/user_id n’existe pas
def save_to_db(annonce_id: int, user_id: int, data: Dict, url: str, image_paths: List[Optional[str]], screenshot_path: str):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Vérifier si le bien immobilier avec cet id et user_id existe
        check_query = "SELECT 1 FROM saved_properties WHERE id = %s AND user_id = %s;"
        cursor.execute(check_query, (annonce_id, user_id))
        result = cursor.fetchone()

        if not result:
            print("Erreur : aucun bien immobilier trouvé avec cet ID et ce User ID.")
            return

        # Mettre à jour uniquement les champs demandés
        update_query = """
        UPDATE saved_properties SET
            url = %s,
            adresse = %s,
            title = %s,
            prix = %s,
            type_habitat = %s,
            surface_habitable = %s,
            surface_terrain = %s,
            nbr_pieces = %s,
            dpe = %s,
            ges = %s,
            description = %s,
            image_paths = %s,
            screenshot_path = %s,
            updated_at = NOW()
        WHERE id = %s AND user_id = %s;
        """

        cursor.execute(update_query, (
            url,
            data.get("adresse"),
            data.get("title"),
            data.get("prix"),
            data.get("type_habitat"),
            data.get("surface_habitable"),
            data.get("surface_terrain"),
            data.get("nbr_pieces"),
            data.get("dpe"),
            data.get("ges"),
            data.get("description"),
            image_paths,
            screenshot_path,
            annonce_id,
            user_id
        ))

        conn.commit()
        print("Bien immobilier mise à jour avec succès.")
    except Exception as e:
        print(f"Erreur lors de la mise à jour du bien immobilier : {str(e)}")
    finally:
        cursor.close()
        conn.close()


# Fonction pour télécharger une image avec gestion automatique des erreurs et des délais
# Paramètre :
#   - url (str) : lien direct de l’image à télécharger
# Retourne :
#   - bytes de l’image si succès, sinon None
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


# Fonction de sauvegarde complète des données issues du scraping
# Paramètres :
#   - incoming_data (Dict) : données extraites du site (titre, adresse, prix, images, etc.)
#   - analyzer (WebScrapingPerformanceAnalyzer) : instance pour le logging des performances
#   - screenshot_success (bool) : indique si la capture d’écran de la page a réussi
#   - url (str) : URL source de l’annonce
#   - timestamp (str) : timestamp utilisé pour créer des noms de fichiers uniques
#   - bien_id (int) : id du bien à mettre à jour
#   - user_id (int) : id de l'utilisateur
# Retourne :
#   - tuple contenant : nombre d’erreurs d’images, nombre total d’images, chemins enregistrés, chemin screenshot
def save_data(
    incoming_data: Dict,
    analyzer: WebScrapingPerformanceAnalyzer,
    screenshot_success: bool,
    url: str,
    timestamp: str,
    annonce_id: int,
    user_id: int
) -> tuple[int, int, List[Optional[str]], str]:
    output_dir = "scraped_data"
    request_dir = f"{output_dir}/{timestamp}"
    os.makedirs(request_dir, exist_ok=True)

    image_paths = []
    image_urls = incoming_data.get('images', {}).get('urls', [])
    error_count = 0

    # BASE_URL à adapter à votre serveur
    BASE_URL = "http://localhost:5001/images"

    for i, image_url in enumerate(image_urls, start=1):
        try:
            image_data = fetch_image(image_url)
            if image_data:
                local_filename = f"image_{timestamp}_{i}.jpeg"
                image_filepath = os.path.join(request_dir, local_filename)
                with open(image_filepath, "wb") as img_file:
                    img_file.write(image_data)
                image_url_served = f"{BASE_URL}/{timestamp}/{local_filename}"
                image_paths.append(image_url_served)
                print(f"Image {i} sauvegardée et accessible via {image_url_served}")
            else:
                image_paths.append(None)
                error_count += 1
        except Exception as e:
            image_paths.append(None)
            error_count += 1
            print(f"Erreur image {i} : {str(e)}")

    incoming_data.pop('image_1', None)
    incoming_data['image_paths'] = image_paths
    incoming_data['screenshot_success'] = screenshot_success

    json_filename = f"{request_dir}/data_{timestamp}.json"
    with open(json_filename, "w", encoding="utf-8") as json_file:
        json.dump(incoming_data, json_file, ensure_ascii=False, indent=4)

    screenshot_filename = f"screenshot_{timestamp}.png"
    screenshot_path_local = os.path.join(request_dir, screenshot_filename)
    screenshot_url = f"{BASE_URL}/{timestamp}/{screenshot_filename}"

    # Appel à save_to_db avec l’URL visible
    save_to_db(annonce_id, user_id, incoming_data, url, image_paths, screenshot_url)

    print(f"Données sauvegardées dans {json_filename}")
    return error_count, len(image_urls), image_paths, screenshot_url


# Fonction pour rechercher un objet dans une liste de dictionnaires selon une valeur clé
# Paramètres :
#   - data (List[Dict]) : liste de dictionnaires à parcourir
#   - key (str) : nom de la clé à comparer
#   - value (str) : valeur recherchée pour la clé spécifiée
# Retourne :
#   - la valeur associée à 'value_label' si trouvée, sinon None
def get_object_by_value(data: List[Dict], key: str, value: str) -> Optional[str]:
    with suppress(TypeError, KeyError):
        for item in data:
            if item.get(key) == value:
                return item.get('value_label')
    return None


# Fonction pour extraire les données d'une annonce depuis une page HTML contenant du JSON embarqué
# Paramètre :
#   - html_content (str) : le contenu HTML brut de la page à analyser
# Retourne :
#   - un dictionnaire contenant les données de l'annonce si trouvé, sinon None
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


# -------------------------------------------------------------------
# Fonction asynchrone de scraping d'une annonce à partir d'une URL.
# Paramètres :
#   - url (str) : URL de la page d’annonce à scraper.
#   - analyzer (WebScrapingPerformanceAnalyzer) : instance pour enregistrer les performances.
#   - bien_id (int) : identifiant du bien immobilier à mettre à jour.
#   - user_id (int) : identifiant de l'utilisateur.
# Résultat :
#   - Un dictionnaire contenant les données extraites de l’annonce, ou None en cas d’échec.
# -------------------------------------------------------------------
async def scrape_search(url: str, analyzer: WebScrapingPerformanceAnalyzer, annonce_id: int, user_id: int) -> Optional[Dict]:
    print(f"Scraping de {url}")
    start_time = time.time()
    request_count = 0
    error_count = 0
    data_points = 0
    response_size = 0
    screenshot_success = False
    node_count = 0

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

                    def handle_request(request):
                        nonlocal node_count
                        node_count += 1
                    page.on("request", handle_request)

                    await page.goto(url, timeout=90000, wait_until="domcontentloaded")
                    request_count += 1

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

                    try:
                        await page.wait_for_selector('script#__NEXT_DATA__', timeout=10000)
                        print("Script __NEXT_DATA__ détecté")
                    except PlaywrightTimeoutError:
                        print("Script __NEXT_DATA__ non détecté, tentative de poursuite")
                        error_count += 1

                    await page.wait_for_timeout(2000)

                    screenshot_path = f"{request_dir}/screenshot_{timestamp}.png"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    print(f"Capture d'écran sauvegardée dans '{screenshot_path}'")
                    screenshot_success = True

                    html_content = await page.content()
                    search_data = parse_search(html_content)

                    if not search_data:
                        raise ValueError("Aucune donnée d'annonce trouvée")

                    response_data = {
                        'adresse': search_data.get("location", {}).get("city_label", None),
                        'title': search_data.get("subject", None),
                        'prix': search_data.get("price_cents", 0)/100 if search_data.get("price_cents") else None,
                        'type_habitat': get_object_by_value(search_data.get("attributes", []), "key", "real_estate_type"),
                        'surface_habitable': extract_number(get_object_by_value(search_data.get("attributes", []), "key", "square")),
                        'surface_terrain': extract_number(get_object_by_value(search_data.get("attributes", []), "key", "land_plot_surface")),
                        'nbr_pieces': get_object_by_value(search_data.get("attributes", []), "key", "rooms"),
                        'dpe': get_object_by_value(search_data.get("attributes", []), "key", "energy_rate"),
                        'ges': get_object_by_value(search_data.get("attributes", []), "key", "ges"),
                        'description': search_data.get("body", None),
                        'images': {"urls": search_data.get('images', {}).get('urls', [])},
                        'image_1': fetch_image(search_data.get('images', {}).get('urls', [None])[0]) if search_data.get('images', {}).get('urls') else None,
                        "html_content": html_content
                    }

                    response_size = len(html_content)
                    img_error_count, img_count, image_paths, screenshot_path = save_data(
                        response_data,
                        analyzer,
                        screenshot_success,
                        url,
                        timestamp,
                        annonce_id,
                        user_id
                    )
                    error_count += img_error_count
                    data_points = sum(1 for v in response_data.values() if v is not None) + img_count
                    success_rate = ((request_count - error_count) / request_count * 100) if request_count > 0 else 0

                    execution_time = time.time() - start_time
                    proxy_count = 1
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
