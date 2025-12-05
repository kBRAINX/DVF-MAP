# seloger_ws_proxy.py
import asyncio
import json
import os
import datetime
import time
import logging
from typing import Dict, Optional, Tuple, List
import re

import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.async_api import async_playwright

from config import proxy, SBR_WS_CDP, WebScrapingPerformanceAnalyzer
from database import DatabaseManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Configuration SSL (utile si proxy d'entreprise en MITM) ---
# Mettre REQUESTS_VERIFY_SSL=false dans l'env pour désactiver la vérification
REQUESTS_VERIFY_SSL = os.getenv("REQUESTS_VERIFY_SSL", "true").lower() == "true"

# Dossier de sortie pour les données/images
OUTPUT_DIR = "scraped_data_seloger"
IMAGES_MOUNT_URL = "http://localhost:5002/images"


def extract_number(value: str) -> Optional[int]:
    """Extrait un entier depuis une chaîne comme '45 m²' → 45"""
    if isinstance(value, str):
        match = re.search(r'\d+', value.replace('\xa0', ' '))
        if match:
            return int(match.group())
    return None


def fetch_image(url: str) -> Optional[bytes]:
    """
    Télécharge une image via requests.
    - Respecte le proxy (si défini dans config.proxy)
    - Vérification SSL configurable via env REQUESTS_VERIFY_SSL
    """
    try:
        response = requests.get(
            url,
            proxies={"http": proxy, "https": proxy},
            timeout=10,
            verify=False  # <--- ignore l'erreur SSL
        )
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Erreur lors du téléchargement de l'image {url} : {e}")
        return None


def save_data(incoming_data: Dict, url: str, annonce_id: str, user_id: int,
              analyzer: WebScrapingPerformanceAnalyzer) -> tuple[int, int]:
    """
    Sauvegarde :
    - Images en local (avec horodatage)
    - JSON brut
    - Mise à jour en base via DatabaseManager
    Retourne (nb_erreurs_image, nb_images)
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    request_dir = os.path.join(OUTPUT_DIR, timestamp)
    os.makedirs(request_dir, exist_ok=True)

    image_paths: List[Optional[str]] = []
    image_urls: List[str] = incoming_data.get('images', {}).get('urls', []) or []
    error_count = 0

    for i, img_url in enumerate(image_urls, start=1):
        img_data = fetch_image(img_url)
        if img_data:
            filename = f"image_{timestamp}_{i}.jpeg"
            filepath = os.path.join(request_dir, filename)
            with open(filepath, "wb") as f:
                f.write(img_data)
            public_url = f"{IMAGES_MOUNT_URL}/{timestamp}/{filename}"
            image_paths.append(public_url)
            logger.info(f"[images] OK -> {public_url}")
        else:
            image_paths.append(None)
            error_count += 1

    incoming_data['image_paths'] = image_paths
    incoming_data['url'] = url

    json_path = os.path.join(request_dir, f"data_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(incoming_data, f, ensure_ascii=False, indent=2)
    logger.info(f"[data] JSON sauvegardé -> {json_path}")

    db_manager = DatabaseManager()
    ok = db_manager.save_to_db(incoming_data, annonce_id, url, user_id)
    if not ok:
        logger.warning("[db] Aucune ligne mise à jour (vérifie id/user_id et schéma).")

    return error_count, len(image_urls)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def scrape_with_retry(url: str) -> Tuple[str, int]:
    """
    Retourne (html, response_size_bytes)
    Retries automatiques (tenacity).
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(SBR_WS_CDP)
        try:
            page = await browser.new_page()
            await page.goto(url, timeout=60_000)
            await page.wait_for_load_state('networkidle')
            content = await page.content()
            return content, len(content.encode("utf-8"))
        finally:
            await browser.close()


def parse_search(content: str) -> Optional[Dict]:
    """
    Parse une page SeLoger (HTML) et extrait les infos principales.
    """
    try:
        soup = BeautifulSoup(content, "html.parser")

        # Dump debug (utile en dev)
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Contenu HTML sauvegardé dans debug.html")

        # Exemple de parse (sensible aux changements du site)
        main_features_div = soup.find("div", string=re.compile(r"\d+ pièces.*\d+ m²"))
        main_features = main_features_div.text.split("•") if main_features_div else []

        characteristics_div = soup.find("div", string="Caractéristiques")
        characteristics = [li.text.strip()
                           for li in (characteristics_div.find_next("ul").find_all("li")
                                      if characteristics_div else [])]

        image_urls = [img.get("src") for img in soup.select("div img") if img.get("src")]

        scale_elements = soup.select("div.css-r92wp3 div[data-testid='cdp-preview-scale-highlighted']")
        dpe_scale = scale_elements[0] if len(scale_elements) > 0 else None
        ges_scale = scale_elements[1] if len(scale_elements) > 1 else None

        if not dpe_scale:
            dpe_div = soup.find("div", string="Diagnostic de performance énergétique (DPE)")
            dpe_scale = dpe_div.find_next("div") if dpe_div else None
        if not ges_scale:
            ges_div = soup.find("div", string="Indice d'émission de gaz à effet de serre (GES)")
            ges_scale = ges_div.find_next("div") if ges_div else None

        type_element = (soup.select_one("span.css-1b9ytm[data-testid='cdp-hardfacts']")
                        or soup.find(lambda tag: tag.name in ["span", "div", "h2"] and
                                     re.search(r".*à vendre", tag.text, re.IGNORECASE)))
        type_habitat = None
        if type_element:
            type_text = type_element.text.strip()
            type_habitat = re.sub(r"à vendre", "", type_text, flags=re.IGNORECASE).strip()

        adresse_div = soup.find("div", string=re.compile(r".*, \w+ \d+.*\(\d+\)"))
        titre_div = soup.find("h2") or soup.find("div", string=re.compile(r"À VENDRE.*"))
        prix_span = soup.select_one("span.css-otf0vo")
        ref_div = soup.find("div", string=re.compile("Référence annonce:"))

        return {
            "adresse": adresse_div.text.strip() if adresse_div else None,
            "titre": titre_div.text.strip() if titre_div else None,
            "prix": extract_number(prix_span.text.strip()) if prix_span else None,
            "type_habitat": type_habitat,
            "surface_habitable": next((f.strip() for f in main_features if "m²" in f and "terrain" not in f), None),
            "surface_terrain": next((c for c in characteristics if "m² de terrain" in c), None),
            "nbr_pieces": extract_number(next((f.strip() for f in main_features if "pièces" in f), None)),
            "dpe": dpe_scale.text.strip() if dpe_scale else None,
            "ges": ges_scale.text.strip() if ges_scale else None,
            "description": (titre_div.find_parent().text.strip()
                            if titre_div and titre_div.find_parent() else None),
            "images": {"urls": image_urls},
            "reference": ref_div.text.replace("Référence annonce:", "").strip() if ref_div else None
        }
    except Exception as e:
        logger.exception(f"[parse] Erreur lors du parsing: {e}")
        return None


async def scrape_search(url: str, annonce_id: str, user_id: int,
                        analyzer: WebScrapingPerformanceAnalyzer) -> Optional[Dict]:
    """
    Scrape une annonce SeLoger, télécharge les images et met à jour la DB.
    """
    logger.info(f"Scraping de l'annonce {url}")
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

        img_error_count, img_count = save_data(search_data, url, annonce_id, user_id, analyzer)
        error_count += img_error_count

        execution_time = time.time() - start_time
        analyzer.log_performance(execution_time, request_count, response_size, proxy_attempts)

        return search_data
    except Exception as e:
        error_count += 1
        execution_time = time.time() - start_time
        analyzer.log_performance(execution_time, request_count, response_size, proxy_attempts)
        logger.exception(f"[scrape] Erreur lors du scraping: {e}")
        return None

