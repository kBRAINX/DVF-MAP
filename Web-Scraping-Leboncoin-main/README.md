# Web-Scraping-Leboncoin
Scripts de Scraping Leboncoin

Ce dépôt contient deux scripts Python pour scraper des annonces immobilières sur Leboncoin, sauvegarder les données dans une base de données PostgreSQL, télécharger des images, et générer des graphiques de performance.

ces differents scripts se trouvent chacun respectivement dans les repertoires suivants:

#### lbc_ws_proxy
lbc_ws_proxy.py : Utilise un proxy Bright Data avec Playwright pour le scraping.

#### lbc_ws_scrapfly
ws_scrapfly_lbc.py : Utilise l'API Scrapfly pour le scraping.

## Prérequis

- Système d'exploitation : Linux, macOS ou Windows.

- Python : Version 3.8 ou supérieure.

- PostgreSQL : Serveur PostgreSQL (version 12 ou supérieure) avec une base de données immo_bd.

- création de comptes tiers :

- Bright Data (pour lbc_ws_proxy.py) : Compte avec accès aux proxies résidentiels et au navigateur de scraping.

- Scrapfly (pour ws_scrapfly_lbc.py) : Compte avec une clé API valide.

# Commande d'initialisation du projet

## Creation et Activation de l'environnement virtuel

```bash
python3 -m venv venv              # Créer un nouvel environnement virtuel

source venv/bin/activate          # Activer l’environnement sous linux

venv\Scripts\activate             # Activer l'environnement sous windows

deactivate                        # Desactiver l'environnement virtuel
```

## Installations des dependances necessaires pour le projet

```bash
pip install -r requirements.txt   # Installer toutes les dépendances listées dans le fichier
```


## Configuration De la base de donnees Postgresql

Base de données PostgreSQL :

- Créez une base de données **immo_bd** :CREATE DATABASE immo_bd;

- Mettez à jour les paramètres de connexion dans chaque script (utilisateur, mot de passe, etc.).

## Services tiers :

- Bright Data : Configurez les identifiants (customer_id, zone, password, BROWSER_AUTH) dans le fichier **.env** de **lbc_ws_proxy**.

- Scrapfly : Configurez la clé API (KEY) dans le fichier **.env** de **lbc_ws_scrapfly**.

## Utilisation

Exécutez l'un des scripts etant dans leur repertoire respectif avec une URL d'annonce Leboncoin en argument :

```bash
python lbc_ws_proxy.py "https://www.leboncoin.fr/ventes_immobilieres/123456789.htm"

ou

python ws_scrapfly_lbc.py "https://www.leboncoin.fr/ventes_immobilieres/123456789.htm"
```

## Les scripts :

- Scrapent les données (adresse, prix, type, etc.).

- Téléchargent les images.

- Sauvegardent les données dans scraped_data/ (JSON, images, captures d'écran pour lbc_ws_proxy.py).

- Enregistrent les données dans la table Annonces de immo_bd.

- Génèrent un graphique de performance (performance_analysis.png).

