require('dotenv').config();
const express = require('express');
const authRoutes = require('./routes/authRoutes');

const app = express();
const PORT = process.env.PORT || 3000;

// CORS - DOIT ÊTRE EN PREMIER avant tout autre middleware
app.use((req, res, next) => {
  console.log(`[CORS] ${req.method} ${req.path} - Origin: ${req.headers.origin}`);
  
  // Headers CORS
  res.setHeader('Access-Control-Allow-Origin', 'http://localhost:4200');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
  res.setHeader('Access-Control-Allow-Credentials', 'true');
  
  // Répondre immédiatement aux requêtes OPTIONS
  if (req.method === 'OPTIONS') {
    console.log('[CORS] Preflight request handled');
    return res.status(200).end();
  }
  
  next();
});

// Middleware pour parser le JSON (APRÈS CORS)
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);

// Route de test
app.get('/', (req, res) => {
  res.json({ 
    message: 'Service d\'authentification actif',
    port: PORT,
    cors: 'Configuré pour localhost:4200'
  });
});

// Gestion des erreurs
app.use((err, req, res, next) => {
  console.error('Erreur serveur:', err.stack);
  res.status(500).json({ message: 'Erreur interne du serveur' });
});

app.listen(PORT, () => {
  console.log(`🚀 Serveur démarré sur le port ${PORT}`);
  console.log(`📡 CORS configuré pour http://localhost:4200`);
  console.log(`🔗 API disponible sur http://localhost:${PORT}/api/auth`);
});

module.exports = app;
