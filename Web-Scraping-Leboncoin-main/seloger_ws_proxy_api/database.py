from typing import Dict
import psycopg2
from psycopg2 import Error
from dotenv import load_dotenv
import os

# Charger les variables d'environnement
load_dotenv()

hostname = os.getenv("POSTGRESQL_HOST", "localhost")
port = os.getenv("POSTGRESQL_PORT", "5432")
database = os.getenv("POSTGRESQL_DATABASE_NAME", "immo_bd")
user = os.getenv("POSTGRESQL_USER", "admin")
password = os.getenv("POSTGRESQL_PASSWORD", "Nuttertools237")

class DatabaseManager:
    """
    Gère la connexion et les opérations sur la base PostgreSQL.
    Ici on effectue uniquement une **mise à jour** d'une annonce.
    """
    def __init__(self):
        self.conn_params = {
            "host": hostname,
            "port": port,
            "database": database,
            "user": user,
            "password": password
        }
        self.conn = None  # Pas de création de table ici

    def connect(self):
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            return True
        except Error as e:
            print(f"Erreur de connexion à la base de données : {e}")
            return False

    def save_to_db(self, data: Dict, annonce_id: str, url: str, user_id: int) -> bool:
        """
        Met à jour une annonce existante dans `saved_properties`
        """
        try:
            if self.connect():
                with self.conn.cursor() as cur:
                    cur.execute("""
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
                            updated_at = NOW()
                        WHERE id = %s AND user_id = %s
                    """, (
                        url,
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
                        annonce_id,
                        user_id
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

