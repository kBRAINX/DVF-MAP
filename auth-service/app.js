const express = require('express');
require('dotenv').config();

const userRoutes = require('./routes/user');

const app = express();

// Configuration CORS temporaire pour debug
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization, Content-Length, X-Requested-With');
  
  if (req.method === 'OPTIONS') {
    res.sendStatus(200);
  } else {
    next();
  }
});

// Middleware pour parser le JSON (APRÈS CORS)
app.use(express.json());

// Routes
app.use('/api/auth', userRoutes);

// Route de base
app.get('/', (req, res) => {
  res.json({
    message: 'Service d\'authentification - API running',
    version: '1.0.0',
    port: process.env.PORT || 3000
  });
});

// Gestion des routes non trouvées
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    message: 'Route non trouvée'
  });
});

// Gestion globale des erreurs
app.use((error, req, res, next) => {
  console.error('Erreur:', error);
  res.status(500).json({
    success: false,
    message: 'Erreur interne du serveur'
  });
});

module.exports = app;
