# Application de Gestion de Projets

Cette application est une solution complète de gestion de projets avec une architecture moderne utilisant Docker.

## 🚀 Structure du Projet

- `frontend/` : Application Angular
- `backend/` : API Flask
- `BD/` : Base de données PostgreSQL
- `nginx/` : Configuration du serveur web
- `docker-compose.yml` : Configuration Docker pour l'ensemble du projet

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir installé :

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [PostgreSQL](https://www.postgresql.org/download/) (pour le développement local)
- [Python](https://www.python.org/downloads/) (pour le backend)
- [Node.js](https://nodejs.org/) (pour le frontend)
- [Angular CLI](https://angular.io/cli)

## 🛠️ Installation et Démarrage en Mode Développement

1. Clonez le dépôt :
   ```bash
   git clone [URL_DU_REPO]
   cd [NOM_DU_PROJET]
   ```

2. Configuration de la Base de Données :
   ```bash
   # Créez une base de données PostgreSQL
   createdb [NOM_DE_LA_BD]
   
   # Importez le schéma de la base de données
   psql [NOM_DE_LA_BD] < BD/dvf_dump.sql
   ```

3. Configuration du Backend (Flask) :
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Sur Windows: venv\Scripts\activate
   pip install -r requirements.txt
   flask run  # Le serveur tournera sur http://localhost:5000
   ```

4. Configuration du Frontend (Angular) :
   ```bash
   cd frontend
   npm install
   ng serve  # L'application tournera sur http://localhost:4200
   ```

## 🌐 Déploiement avec Docker

Pour déployer l'application en production :

1. Assurez-vous que Docker et Docker Compose sont installés sur votre serveur

2. Clonez le dépôt sur votre serveur :
   ```bash
   git clone [URL_DU_REPO]
   cd [NOM_DU_PROJET]
   ```

3. Lancez l'application avec Docker Compose :
   ```bash
   docker-compose up -d
   ```

   Cette commande va :
   - Construire et démarrer tous les services
   - Configurer la base de données PostgreSQL
   - Démarrer le serveur Flask
   - Démarrer l'application Angular
   - Configurer Nginx comme reverse proxy

4. L'application sera accessible à :
   - Frontend : http://localhost:80
   - Backend API : http://localhost:80/api

## 🔧 Configuration des Ports

- Frontend (Angular) : 4200 (développement) / 80 (production)
- Backend (Flask) : 5000 (développement) / 80 (production)
- Base de données (PostgreSQL) : 5432

## 📝 Développement

### Backend (Flask)
- Port : 5000
- Environnement virtuel requis
- Commandes principales :
  ```bash
  cd backend
  source venv/bin/activate  # Sur Windows: venv\Scripts\activate
  flask run
  ```

### Frontend (Angular)
- Port : 4200
- Commandes principales :
  ```bash
  cd frontend
  npm install
  ng serve
  ```

## 🤝 Contribution

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request
