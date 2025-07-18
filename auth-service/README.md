# Service d'Authentification

Service d'authentification simple avec Express.js, PostgreSQL et JWT.

## Fonctionnalités

- ✅ Inscription d'utilisateur
- ✅ Connexion avec JWT
- ✅ Récupération du profil utilisateur
- ✅ Middleware d'authentification
- ✅ Hachage sécurisé des mots de passe
- ✅ Configuration via variables d'environnement

## Prérequis

- Node.js (version LTS)
- PostgreSQL
- npm ou yarn

## Installation

1. **Cloner le projet**
```bash
git clone <url-du-repo>
cd auth-service
```

2. **Installer les dépendances**
```bash
npm install
```

3. **Configuration de l'environnement**
```bash
cp .env.example .env
```
Modifier le fichier `.env` avec vos paramètres de base de données.

4. **Créer la base de données PostgreSQL et la configurer**
```bash
psql -U [USERNAME_PSQL] -d auth -f database.sql

#la base de donnees est auth_db
```

5. **Generer la cle secrete**
```bash
node generate-secret.js
```

5. **Lancer le serveur**
```bash
# En mode développement
npm run dev

# En mode production
npm start
```

Le serveur sera accessible sur `http://localhost:3001`

## Routes API

### Inscription
```
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "motdepasse123"
}
```

### Connexion
```
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "motdepasse123"
}
```

### Profil utilisateur (authentifié)
```
GET /api/auth/profile
Authorization: Bearer <token>
```

## Réponses API

### Succès
```json
{
  "success": true,
  "message": "Message de succès",
  "user": { ... },
  "token": "jwt_token"
}
```

### Erreur
```json
{
  "success": false,
  "message": "Message d'erreur"
}
```

## Variables d'environnement

```env
# Serveur
PORT=3001

# Base de données
DB_USER=votre_utilisateur
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432
DB_NAME=DB_NAME

# JWT
JWT_SECRET=votre_clé_secrète_très_sécurisée
```

## Structure du projet

```
auth-service/
├── .env                    # Variables d'environnement
├── .gitignore             # Fichiers à ignorer
├── package.json           # Dépendances et scripts
├── server.js              # Point d'entrée du serveur
├── app.js                 # Configuration Express
├── config/
│   └── database.js        # Configuration base de données
├── middleware/
│   └── auth.js            # Middleware d'authentification
├── controllers/
│   └── user.js            # Logique métier utilisateur
└── routes/
    └── user.js            # Routes utilisateur
```

## Sécurité

- Les mots de passe sont hachés avec bcrypt (cost factor: 12)
- Les tokens JWT expirent après 24h
- Validation des données d'entrée
- Protection CORS configurée

## Tests avec curl

### Inscription
```bash
curl -X POST http://localhost:3001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'
```

### Connexion
```bash
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"123456"}'
```

### Profil (remplacer TOKEN par le token reçu)
```bash
curl -X GET http://localhost:3001/api/auth/profile \
  -H "Authorization: Bearer TOKEN"
```
