import jwt
from flask import request, jsonify
from functools import wraps
import os

# Secret JWT (à mettre dans .env)
JWT_SECRET = os.getenv("JWT_SECRET", "change_this_in_production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def extract_user_id_from_bearer_token():
    """
    Tente d'extraire user_id (ou sub) depuis le token JWT dans Authorization header.
    Retourne int user_id ou None si échec.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None, "Header Authorization manquant."

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None, "Format d'Authorization invalide. Utiliser 'Bearer <token>'."

    token = parts[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False})
        user_id = payload.get("id") or payload.get("sub")
        if not user_id:
            return None, "user_id introuvable dans le token."
        return int(user_id), None
    except jwt.DecodeError:
        return None, "Token invalide."
    except Exception as e:
        # Par exemple expiration si tu veux la vérifier, etc.
        return None, f"Erreur lors du décodage du token: {str(e)}"

