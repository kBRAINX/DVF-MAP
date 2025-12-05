import os
import datetime
import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv()

# Configuration Bright Data pour les proxies HTTP (pour les images uniquement)
customer_id = os.getenv("BRIGHT_DATA_CUSTOMER_ID", "hl_341de7f4")
zone = os.getenv("BRIGHT_DATA_ZONE", "residential_proxy1")
password = os.getenv("BRIGHT_DATA_PASSWORD", "b0q6na4fz3nz")
proxy_host = os.getenv("BRIGHT_DATA_PROXY_HOST", "brd.superproxy.io")
proxy_port = os.getenv("BRIGHT_DATA_PROXY_PORT", 33335)
proxy = f"http://brd-customer-{customer_id}-zone-{zone}:{password}@{proxy_host}:{proxy_port}"


# Configuration Bright Data pour le navigateur
BROWSER_AUTH = os.getenv("BRIGHT_DATA_BROWSER_AUTH", "brd-customer-hl_341de7f4-zone-residential_proxy1-password-b0q6na4fz3nz")
if not BROWSER_AUTH:
    raise ValueError("La variable d'environnement BRIGHT_DATA_BROWSER_AUTH n'est pas définie. Veuillez la configurer dans le fichier .env.")

# URL du WebSocket pour le navigateur Bright Data
SBR_WS_CDP = f'wss://{BROWSER_AUTH}@brd.superproxy.io:9222'

# Configuration de la base de données PostgreSQL
hostname = os.getenv("POSTGRESQL_HOST", "localhost")
port = os.getenv("POSTGRESQL_PORT", "5432")
database = os.getenv("POSTGRESQL_DATABASE_NAME", "immo_bd")
user = os.getenv("POSTGRESQL_USER", "admin")
password = os.getenv("POSTGRESQL_PASSWORD", "Nuttertools237")

# Configuration de la base de données PostgreSQL
DB_CONFIG = {
    "host": hostname,
    "port": port,
    "database": database,
    "user": user,
    "password": password
}

# Classe d'analyse des performances d'une session de web scraping
# Aucun paramètre n’est requis pour l’instanciation
# Elle initialise une structure de données pour enregistrer et visualiser les performances du scraping
class WebScrapingPerformanceAnalyzer:

    # Constructeur qui initialise le dictionnaire de stockage des métriques de performances
    # Aucun paramètre requis
    # Initialise une structure de stockage vide pour les données de performance
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

    # Méthode pour enregistrer les métriques d’une session de scraping
    # Paramètres : execution_time (float), request_count (int), error_count (int),
    # data_points (int), success_rate (float), response_size (int),
    # screenshot_success (bool), proxy_count (int), node_count (int)
    # Remplit la structure de données avec les métriques fournies
    def log_performance(self, execution_time: float, request_count: int,
                        error_count: int, data_points: int,
                        success_rate: float, response_size: int,
                        screenshot_success: bool, proxy_count: int, node_count: int):
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

    # Méthode pour générer et sauvegarder des graphiques basés sur les performances enregistrées
    # Paramètre : output_file (str) — nom du fichier image de sortie (par défaut "performance_analysis.png")
    # Retourne une chaîne de confirmation ou un message d’erreur si aucune donnée n’est disponible
    def plot_performance_metrics(self, output_file: str = "performance_analysis.png") -> str:
        df = pd.DataFrame(self.performance_data)
        if df.empty:
            return "Aucune donnée pour générer les graphiques"

        plt.figure(figsize=(15, 15))

        # Graphique 1 : Temps d'exécution vs nombre de requêtes
        plt.subplot(3, 1, 1)
        plt.scatter(df['request_counts'], df['execution_times'], color='b', marker='o')
        plt.title('Temps d\'exécution en fonction du nombre de requêtes')
        plt.xlabel('Nombre de requêtes')
        plt.ylabel('Temps (secondes)')
        plt.grid(True)

        # Graphique 2 : Taille des réponses vs nombre de requêtes
        plt.subplot(3, 1, 2)
        plt.scatter(df['request_counts'], df['response_sizes'], color='g', marker='o')
        plt.title('Volume des données échangées en fonction du nombre de requêtes')
        plt.xlabel('Nombre de requêtes')
        plt.ylabel('Taille des réponses (octets)')
        plt.grid(True)

        # Graphique 3 : Proxies et nœuds parcourus vs nombre de requêtes
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

# Fonction pour initialiser la base de données avec une table 'Annonces'
# Aucun paramètre requis ; utilise une configuration externe (DB_CONFIG)
# Crée la table 'Annonces' dans la base de données PostgreSQL si elle n'existe pas déjà
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
