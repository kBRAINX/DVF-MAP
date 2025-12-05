+----------------------------------------------------+
+README - Script de Scraping Leboncoin avec Scrapfly +
+----------------------------------------------------+

Ce script Python (ws_scrapfly_lbc.py) permet de scraper des annonces immobilières sur Leboncoin en utilisant l'API Scrapfly, de sauvegarder les données dans une base de données PostgreSQL, de télécharger des images, et de générer des graphiques d'analyse de performance.

Prérequis
---------
### Prérequis
-------------
- **Acceder au repertoire du script**
```bash
cd lbc_ws_scrapfly
```

- **Creation du fichier des variables d'environement**
```bash
cp .env.example .env 
```

- **PostgreSQL** : Installez et configurez un serveur PostgreSQL (version 12 ou supérieure).
Compte Scrapfly :
Créez un compte sur [Scrapfly](https://scrapfly.io/) et obtenez une clé API.

### Configuration
------------------

- **Configuration Scrapfly**
Remplacez la clé API dans le fichier **.env** crée précedement

- **Base de données PostgreSQL** :
Créez une base de données nommée **immo_bd** si elle n'est pas encore crée.
ensuite renseigner toutes les informations necessaire a la configuraion de la dase de données dans la section adequate du fichier **.env**

```bash
POSTGRESQL_HOST=localhost
POSTGRESQL_PROST=5432
POSTGRESQL_DATABASE_NAME=DATABASE_NAME
POSTGRESQL_USER=USERNAME
POSTGRESQL_PASSWORD=PASSWORD
```

Assurez-vous que le serveur PostgreSQL est en cours d'exécution.


### Dossier de sortie :
Le script crée un dossier scraped_data pour stocker les JSON et les images.
Assurez-vous que l'utilisateur a les permissions d'écriture dans le répertoire de travail.


### Utilisation

Exécutez le script avec une URL d'annonce Leboncoin en argument :

```bash
python ws_scrapfly_lbc.py "https://www.leboncoin.fr/ventes_immobilieres/123456789.htm"
```

### Le script :
- Scrape les données de l'annonce (adresse, prix, type, surface, etc.) via Scrapfly.
- Télécharge les images associées.
- Sauvegarde les données dans scraped_data/data_<timestamp>.json et les images dans scraped_data/image_<timestamp>_<num>.jpeg.
- Enregistre les données dans la table Annonces de immo_bd.
- Génère un graphique de performance (performance_analysis.png).



### Résultats

- **Données** : Sauvegardées dans scraped_data/data_<timestamp>.json.
- **Images** : Sauvegardées dans scraped_data/image_<timestamp>_<num>.jpeg.
- **Base de données** : Données insérées dans la table Annonces de immo_bd.
- **Graphique** : Graphique de performance dans performance_analysis.png.

### Dépannage

Erreur de connexion PostgreSQL : Vérifiez les identifiants dans conn_params et assurez-vous que le serveur est en cours d'exécution.
Erreur Scrapfly : Vérifiez la clé API et le solde de votre compte Scrapfly.
Timeout ou erreurs réseau : Vérifiez la connexion réseau ou augmentez le délai dans SCRAPFLY.async_scrape (timeout=15).
Images non téléchargées : Vérifiez les permissions d'écriture et l'URL des images.

### Notes

Le script utilise l'AOI Scrapfly avec la configuration public_residential_pool et le pays fr.
Une seule page est scrapée par exécution (max_pages=1).
Les erreurs de scraping ou de téléchargement d'images sont enregistrées dans les métriques de performance.

