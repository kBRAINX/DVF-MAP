import datetime
import os
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# Charger le fichier .env
load_dotenv()

# Configuration Bright Data
customer_id = os.getenv("BRIGHT_DATA_CUSTOMER_ID", "hl_d2d90740")
zone = os.getenv("BRIGHT_DATA_ZONE", "residential_proxy1")
password = os.getenv("BRIGHT_DATA_PASSWORD", "6rdsqopy5yrg")
proxy_host = os.getenv("BRIGHT_DATA_PROXY_HOST", "brd.superproxy.io")
proxy_port = os.getenv("BRIGHT_DATA_PROXY_PORT", 33335)
proxy = f"http://brd-customer-{customer_id}-zone-{zone}:{password}@{proxy_host}:{proxy_port}"

# Configuration Bright Data pour le navigateur
BROWSER_AUTH = os.getenv("BRIGHT_DATA_BROWSER_AUTH", "brd-customer-hl_d2d90740-zone-scraping_browser1:x86w4rrdc83a")
if not BROWSER_AUTH:
    raise ValueError("La variable d'environnement BRIGHT_DATA_BROWSER_AUTH n'est pas définie. Veuillez la configurer dans le fichier .env.")

# URL du WebSocket pour le navigateur Bright Data
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
