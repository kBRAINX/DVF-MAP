from flask import Flask, request, jsonify
from flasgger import Swagger
from db_config import get_connection
from flask_cors import CORS

app = Flask(__name__)
# Configuration CORS sécurisée pour la production
CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost",
            "http://localhost:80",
            "http://localhost:4200",
            "http://51.20.250.121",
            "http://51.20.250.121:80",
            "http://dvf-map-irt.duckdns.org",
            "https://dvf-map-irt.duckdns.org"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

app.config['SWAGGER'] = {
    'title': 'DVF API',
    'uiversion': 3
}
swagger = Swagger(app)

@app.route('/api/v1/dvf/ventes', methods=['GET'])
def get_dvf_ventes():
    """
    Récupération des ventes DVF (maisons)
    ---
    parameters:
      - name: topLeft
        in: query
        type: string
        required: true
        description: Coin haut-gauche (lat,long)
      - name: bottomRight
        in: query
        type: string
        required: true
        description: Coin bas-droit (lat,long)
      - name: price
        in: query
        type: string
        required: false
        description: Valeur foncière min,max
      - name: date
        in: query
        type: string
        required: false
        description: Dates de mutation min,max (YYYY-MM-DD)
    responses:
      200:
        description: Liste des biens vendus filtrés
    """
    try:
        top_left_raw = request.args.get('topLeft')
        bottom_right_raw = request.args.get('bottomRight')
        if not top_left_raw or not bottom_right_raw:
            return jsonify({"error": "Les paramètres 'topLeft' et 'bottomRight' sont requis."}), 400

        top_left = top_left_raw.replace(" ", "").split(',')
        bottom_right = bottom_right_raw.replace(" ", "").split(',')

        # Debug: Print the raw coordinates
        print(f"Raw coordinates: topLeft={top_left}, bottomRight={bottom_right}")

        # Coordinates are in Lambert93 format (y,x) where y is latitude and x is longitude
        # The frontend sends them as (y,x) but we need to extract them correctly
        try:
            # Extract coordinates - assuming format is [y, x] for both points
            y_max, x_min = float(top_left[0]), float(top_left[1])
            y_min, x_max = float(bottom_right[0]), float(bottom_right[1])

            # For database query, we need latitude (y) and longitude (x)
            lat_min, lat_max = y_min, y_max
            lon_min, lon_max = x_min, x_max

            print(f"Parsed coordinates: lat_min={lat_min}, lat_max={lat_max}, lon_min={lon_min}, lon_max={lon_max}")
        except (ValueError, IndexError) as e:
            return jsonify({"error": f"Format de coordonnées invalide: {str(e)}"}), 400

        price_param = request.args.get('price')
        date_param = request.args.get('date')

        conn = get_connection()
        cursor = conn.cursor()

        # First, check if we have any houses in the database with coordinates
        check_query = "SELECT COUNT(*) FROM dvf WHERE type_local = 'Maison' AND latitude IS NOT NULL AND longitude IS NOT NULL"
        cursor.execute(check_query)
        total_houses = cursor.fetchone()[0]
        print(f"Total houses with coordinates in database: {total_houses}")

        # Check the range of coordinates in the database
        range_query = "SELECT MIN(latitude), MAX(latitude), MIN(longitude), MAX(longitude) FROM dvf WHERE type_local = 'Maison' AND latitude IS NOT NULL AND longitude IS NOT NULL"
        cursor.execute(range_query)
        coord_range = cursor.fetchone()
        print(f"Coordinate range in database: lat_min={coord_range[0]}, lat_max={coord_range[1]}, lon_min={coord_range[2]}, lon_max={coord_range[3]}")

        # Get pagination parameters
        limit = request.args.get('limit', '200')  # Default to 100 results
        offset = request.args.get('offset', '0')  # Default to first page

        try:
            limit = int(limit)
            offset = int(offset)
            # Cap the limit to a reasonable value to prevent performance issues
            if limit > 500:
                limit = 500
        except ValueError:
            limit = 100
            offset = 0

        # Try a simplified query first to see if we have any properties in the database
        test_query = "SELECT COUNT(*) FROM dvf WHERE type_local = 'Maison'"
        cursor.execute(test_query)
        total_houses = cursor.fetchone()[0]
        print(f"Total houses in database: {total_houses}")

        # Modify query to be more flexible with coordinates
        query = """
            SELECT id_mutation, valeur_fonciere, date_mutation, latitude, longitude,
                   adresse_numero, adresse_nom_voie, code_postal, nom_commune,id_parcelle,surface_terrain
            FROM dvf
            WHERE type_local = 'Maison'
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
              AND valeur_fonciere IS NOT NULL
              AND date_mutation IS NOT NULL
        """
        params = []

        # For testing purposes, let's be very flexible with coordinates
        # We'll expand the bounding box by 20% to ensure we find some properties
        if lat_min > -90 and lat_max < 90 and lon_min > -180 and lon_max < 180:
            # Calculate the center of the bounding box
            lat_center = (lat_min + lat_max) / 2
            lon_center = (lon_min + lon_max) / 2

            # Calculate the dimensions of the bounding box
            lat_range = abs(lat_max - lat_min)
            lon_range = abs(lon_max - lon_min)

            # Expand the bounding box by 20%
            expanded_lat_min = lat_center - (lat_range * 0.6)
            expanded_lat_max = lat_center + (lat_range * 0.6)
            expanded_lon_min = lon_center - (lon_range * 0.6)
            expanded_lon_max = lon_center + (lon_range * 0.6)

            print(f"Original bounding box: lat_min={lat_min}, lat_max={lat_max}, lon_min={lon_min}, lon_max={lon_max}")
            print(f"Expanded bounding box: lat_min={expanded_lat_min}, lat_max={expanded_lat_max}, lon_min={expanded_lon_min}, lon_max={expanded_lon_max}")

            query += """
              AND latitude BETWEEN %s AND %s
              AND longitude BETWEEN %s AND %s
            """
            params.extend([expanded_lat_min, expanded_lat_max, expanded_lon_min, expanded_lon_max])

        # Don't apply a default price filter to ensure we get some results
        if not price_param:
            print("No price filter applied - showing all prices")

        if price_param and ',' in price_param:
            price_min, price_max = map(float, price_param.replace(" ", "").split(','))
            if price_min == price_max:
                query += " AND valeur_fonciere = %s"
                params.append(price_min)
            else:
                query += " AND valeur_fonciere BETWEEN %s AND %s"
                params.extend([price_min, price_max])

        if date_param and ',' in date_param:
            date_min, date_max = date_param.replace(" ", "").split(',')
            if date_min == date_max:
                query += " AND date_mutation = %s"
                params.append(date_min)
            else:
                query += " AND date_mutation BETWEEN %s AND %s"
                params.extend([date_min, date_max])

        # Add ORDER BY, LIMIT and OFFSET to the query
        query += """
            ORDER BY valeur_fonciere DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])

        print("REQUÊTE:", cursor.mogrify(query, params))  # log SQL pour debug

        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            print(f"Nombre de résultats trouvés: {len(rows)} (limit={limit}, offset={offset})")

            # If we have results, print a sample for debugging
            if rows:
                print(f"Premier résultat: {rows[0]}")

            result = []
            for r in rows:
                # Check if we have enough columns in the result
                if len(r) >= 9:
                    property_data = {
                        "id_mutation": r[0],
                        "valeur_fonciere": float(r[1]) if r[1] is not None else 0,
                        "date_mutation": str(r[2]) if r[2] is not None else "",
                        "latitude": float(r[3]) if r[3] is not None else 0,
                        "longitude": float(r[4]) if r[4] is not None else 0,
                        "adresse_numero": r[5] if r[5] is not None else "",
                        "adresse_nom_voie": r[6] if r[6] is not None else "",
                        "code_postal": r[7] if r[7] is not None else "",
                        "nom_commune": r[8] if r[8] is not None else "",
                        "id_parcelle": r[9] or "",
                        "surface_terrain": float(r[10]) if r[10] is not None else None
                    }
                else:
                    # Fallback for older query format
                    property_data = {
                        "id_mutation": r[0],
                        "valeur_fonciere": float(r[1]) if r[1] is not None else 0,
                        "date_mutation": str(r[2]) if r[2] is not None else "",
                        "latitude": float(r[3]) if r[3] is not None else 0,
                        "longitude": float(r[4]) if r[4] is not None else 0
                    }
                result.append(property_data)

            if not result:
                print("Aucun bien trouvé avec ces filtres.")
                return jsonify({"message": "Aucun bien trouvé avec ces filtres."}), 200

            print(f"Retour de {len(result)} propriétés.")
            return jsonify(result)

        except Exception as e:
            print(f"Erreur lors de l'exécution de la requête: {str(e)}")
            return jsonify({"error": "Erreur lors de l'exécution de la requête", "details": str(e)}), 500
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        return jsonify({"error": "Erreur serveur", "debug": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

