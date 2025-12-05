import psycopg2
from psycopg2 import Error
from typing import Dict
import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Configuration de la base de données PostgreSQL
hostname = os.getenv("POSTGRESQL_HOST", "localhost")
port = os.getenv("POSTGRESQL_PORT", "5432")
database = os.getenv("POSTGRESQL_DATABASE_NAME", "immo_bd")
user = os.getenv("POSTGRESQL_USER", "admin")
password = os.getenv("POSTGRESQL_PASSWORD", "Nuttertools237")

class DatabaseManager:
    def __init__(self):
        # Paramètres de connexion à la base de données
        self.conn_params = {
            "host": hostname,
            "port": port,
            "database": database,
            "user": user,
            "password": password
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
