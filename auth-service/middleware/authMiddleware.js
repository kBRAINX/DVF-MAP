const jwt = require('jsonwebtoken');
const asyncHandler = require('express-async-handler');

/**
 * Middleware pour protéger les routes
 * Vérifie la présence et la validité du token JWT
 */
const protect = asyncHandler(async (req, res, next) => {
  let token;

  console.log('[AUTH] Headers authorization:', req.headers.authorization);

  if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
    try {
      // Extraire le token du header Authorization
      token = req.headers.authorization.split(' ')[1];
      console.log('[AUTH] Token extrait:', token ? 'Présent' : 'Absent');

      // Vérifier le token
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      console.log('[AUTH] Token décodé, userId:', decoded.id);

      // Ajouter l'ID utilisateur à la requête pour les prochains middlewares
      req.userId = decoded.id;

      next();
    } catch (error) {
      console.error('[AUTH] Erreur de vérification du token:', error.message);

      if (error.name === 'TokenExpiredError') {
        return res.status(401).json({ message: 'Token expiré' });
      } else if (error.name === 'JsonWebTokenError') {
        return res.status(401).json({ message: 'Token invalide' });
      }

      return res.status(401).json({ message: 'Non autorisé' });
    }
  } else {
    console.log('[AUTH] Pas de token fourni');
    return res.status(401).json({ message: 'Non autorisé, pas de token fourni' });
  }
});

module.exports = { protect };
