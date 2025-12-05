import matplotlib.pyplot as plt
import pandas as pd
import datetime

class WebScrapingPerformanceAnalyzer:
    def __init__(self):
        # Initialisation des métriques de performance
        self.performance_data = {
            'timestamps': [],          # Horodatages des sessions
            'execution_times': [],     # Temps d'exécution
            'request_counts': [],      # Nombre de requêtes
            'response_sizes': [],      # Taille des réponses
            'proxy_attempts': []       # Tentatives de proxy
        }

    def log_performance(self, execution_time: float, request_count: int,
                       response_size: int, proxy_attempts: int):
        """Enregistre les métriques de performance pour une session de scraping"""
        self.performance_data['timestamps'].append(datetime.datetime.now())
        self.performance_data['execution_times'].append(execution_time)
        self.performance_data['request_counts'].append(request_count)
        self.performance_data['response_sizes'].append(response_size)
        self.performance_data['proxy_attempts'].append(proxy_attempts)

    def plot_performance_metrics(self, output_file: str = "performance_analysis.png") -> str:
        """Génère et sauvegarde les graphiques d'analyse de performance"""
        df = pd.DataFrame(self.performance_data)
        if df.empty:
            return "Aucune donnée pour générer les graphiques"

        plt.figure(figsize=(15, 10))

        # Graphique 1 : Temps d'exécution vs nombre de requêtes
        plt.subplot(3, 1, 1)
        plt.plot(df['request_counts'], df['execution_times'], 'b-', marker='o')
        plt.title('Temps d\'exécution vs Nombre de requêtes')
        plt.xlabel('Nombre de requêtes')
        plt.ylabel('Temps d\'exécution (secondes)')
        plt.grid(True)

        # Graphique 2 : Histogramme du volume de données
        plt.subplot(3, 1, 2)
        plt.hist(df['response_sizes'], bins=20, color='g', edgecolor='black')
        plt.title('Distribution du volume de données par requête')
        plt.xlabel('Taille de la réponse (octets)')
        plt.ylabel('Fréquence')
        plt.grid(True, alpha=0.3)

        # Graphique 3 : Tentatives de proxy vs nombre de requêtes
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
