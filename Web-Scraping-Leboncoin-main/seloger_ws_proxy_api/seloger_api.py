# seloger_api.py
import asyncio
import logging
import os

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flasgger import Swagger
from dotenv import load_dotenv

from config import WebScrapingPerformanceAnalyzer
from seloger_ws_proxy import scrape_search   # <-- nom du module ci-dessus
from auth_utils import extract_user_id_from_bearer_token

load_dotenv()

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost",
            "http://localhost:80",
            "http://localhost:4200",
            "http://10.144.208.233:4200",
            "http://51.20.250.121",
            "http://51.20.250.121:80",
            "http://dvf-map-irt.duckdns.org",
            "https://dvf-map-irt.duckdns.org"
        ],
        "methods": ["GET", "POST", "PUT", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})
app.config['SWAGGER'] = {'title': 'Scraping API', 'uiversion': 3}
swagger = Swagger(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sert les images écrites par le scraper
@app.route('/images/<path:filename>')
def serve_image(filename):
    image_dir = os.path.join(os.getcwd(), 'scraped_data_seloger')
    return send_from_directory(image_dir, filename)

@app.route("/api/v1/scrape-seloger", methods=["PUT"])
def scrape_seloger_endpoint():
    """
    Scrape une URL SeLoger et met à jour l'annonce en DB (user_id depuis JWT).
    ---
    put:
      summary: Scraping + update d'annonce (SeLoger)
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                url:
                  type: string
                  description: URL complète de l'annonce SeLoger
                  example: "https://www.seloger.com/annonces/achat/appartement/paris-18eme-75/grandes-carrieres-clichy/247803591.htm"
                id:
                  type: integer
                  description: ID interne (table saved_properties)
                  example: 123
              required:
                - url
                - id
      parameters:
        - name: Authorization
          in: header
          description: "Bearer <JWT>"
          required: true
          schema:
            type: string
            example: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      responses:
        200:
          description: Résultat du scraping et métriques
        400:
          description: Requête mal formée
        500:
          description: Erreur interne
    """
    logger.info(f"Headers reçus: {dict(request.headers)}")
    try:
        payload = request.get_json(force=True, silent=False)
    except Exception as e:
        logger.error(f"Erreur parsing JSON: {e}")
        return jsonify({"error": "JSON invalide", "details": str(e)}), 400

    logger.info(f"Payload reçu: {payload}")

    if not payload:
        return jsonify({"error": "Payload JSON attendu."}), 400

    url = payload.get("url")
    annonce_id = payload.get("id")

    if not url or annonce_id is None:
        return jsonify({"error": "Champs 'url' et 'id' requis.",
                        "received": {"url": url, "id": annonce_id}}), 400

    # Auth (extrait user_id à partir du header Authorization)
    user_id, err = extract_user_id_from_bearer_token()
    if user_id is None:
        return jsonify({"error": "Impossible d'extraire user_id depuis token.", "details": err}), 400

    analyzer = WebScrapingPerformanceAnalyzer()

    try:
        response = asyncio.run(scrape_search(url=url, annonce_id=annonce_id, user_id=user_id, analyzer=analyzer))
        scraping_success = response is not None
        message = "Scraping réussi" if scraping_success else "Échec du scraping"
        metrics = analyzer.plot_performance_metrics() if hasattr(analyzer, "plot_performance_metrics") else None

        return jsonify({
            "scraping_success": scraping_success,
            "message": message,
            "metrics": metrics,
            "data": response
        }), 200
    except Exception as e:
        logger.exception("Erreur inattendue lors du scraping")
        return jsonify({"error": f"Erreur inattendue: {str(e)}"}), 500


if __name__ == "__main__":
    # Porte d’écoute (doit correspondre à ce que tu ouvres sur le firewall / security group)
    app.run(host="0.0.0.0", port=5002, debug=True)

