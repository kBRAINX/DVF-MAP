const asyncHandler = require('express-async-handler');
const jwt = require('jsonwebtoken');
const pool = require('../config/database');
const { hashPassword, comparePassword } = require('../utils/hashPassword');

/**
 * Générer un token JWT
 * @param {number} id - L'ID de l'utilisateur
 * @returns {string} - Le token JWT
 */
const generateToken = (id) => {
  return jwt.sign({ id }, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRES_IN || '24h',
  });
};

/**
 * Valider l'email
 * @param {string} email - L'email à valider
 * @returns {boolean} - True si l'email est valide
 */
const isValidEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Valider le mot de passe
 * @param {string} password - Le mot de passe à valider
 * @returns {boolean} - True si le mot de passe est valide
 */
const isValidPassword = (password) => {
  return password && password.length >= 6;
};

// @desc    Inscription d'un utilisateur
// @route   POST /api/auth/register
// @access  Public
const registerUser = asyncHandler(async (req, res) => {
  console.log('[REGISTER] Requête reçue:', req.body);
  
  const { email, password, firstName, lastName } = req.body;

  // Validation des données
  if (!email || !password) {
    console.log('[REGISTER] Erreur: Email et mot de passe requis');
    return res.status(400).json({ message: 'Email et mot de passe requis' });
  }

  if (!isValidEmail(email)) {
    console.log('[REGISTER] Erreur: Format email invalide');
    return res.status(400).json({ message: 'Format d\'email invalide' });
  }

  if (!isValidPassword(password)) {
    console.log('[REGISTER] Erreur: Mot de passe trop court');
    return res.status(400).json({ message: 'Le mot de passe doit contenir au moins 6 caractères' });
  }

  try {
    // Vérifier si l'utilisateur existe déjà
    const userExists = await pool.query('SELECT * FROM users WHERE email = $1', [email.toLowerCase()]);

    if (userExists.rows.length > 0) {
      console.log('[REGISTER] Erreur: Utilisateur existe déjà');
      return res.status(400).json({ message: 'Cet utilisateur existe déjà' });
    }

    // Hacher le mot de passe
    const hashedPassword = await hashPassword(password);

    // Créer l'utilisateur
    const result = await pool.query(
      'INSERT INTO users (email, password, first_name, last_name) VALUES ($1, $2, $3, $4) RETURNING id, email, first_name, last_name, created_at',
      [email.toLowerCase(), hashedPassword, firstName || null, lastName || null]
    );

    const user = result.rows[0];

    if (user) {
      const token = generateToken(user.id);
      console.log('[REGISTER] Succès: Utilisateur créé avec ID', user.id);
      
      res.status(201).json({
        id: user.id,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name,
        token: token,
      });
    } else {
      console.log('[REGISTER] Erreur: Impossible de créer utilisateur');
      res.status(400).json({ message: 'Impossible de créer l\'utilisateur' });
    }
  } catch (error) {
    console.error('[REGISTER] Erreur:', error);
    res.status(500).json({ message: 'Erreur interne du serveur' });
  }
});

// @desc    Connexion d'un utilisateur
// @route   POST /api/auth/login
// @access  Public
const loginUser = asyncHandler(async (req, res) => {
  console.log('[LOGIN] Requête reçue:', { email: req.body.email });
  
  const { email, password } = req.body;

  // Validation des données
  if (!email || !password) {
    return res.status(400).json({ message: 'Email et mot de passe requis' });
  }

  if (!isValidEmail(email)) {
    return res.status(400).json({ message: 'Format d\'email invalide' });
  }

  try {
    // Vérifier si l'utilisateur existe
    const result = await pool.query('SELECT * FROM users WHERE email = $1', [email.toLowerCase()]);
    const user = result.rows[0];

    if (user && (await comparePassword(password, user.password))) {
      const token = generateToken(user.id);
      console.log('[LOGIN] Succès: Connexion utilisateur ID', user.id);
      
      res.json({
        id: user.id,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name,
        token: token,
      });
    } else {
      console.log('[LOGIN] Erreur: Identifiants incorrects');
      res.status(401).json({ message: 'Email ou mot de passe incorrect' });
    }
  } catch (error) {
    console.error('[LOGIN] Erreur:', error);
    res.status(500).json({ message: 'Erreur interne du serveur' });
  }
});

// @desc    Obtenir le profil utilisateur
// @route   GET /api/auth/profile
// @access  Private
const getUserProfile = asyncHandler(async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT id, email, first_name, last_name, created_at, updated_at FROM users WHERE id = $1',
      [req.userId]
    );

    const user = result.rows[0];

    if (user) {
      res.json({
        id: user.id,
        email: user.email,
        firstName: user.first_name,
        lastName: user.last_name,
        createdAt: user.created_at,
        updatedAt: user.updated_at,
      });
    } else {
      res.status(404).json({ message: 'Utilisateur non trouvé' });
    }
  } catch (error) {
    console.error('[PROFILE] Erreur:', error);
    res.status(500).json({ message: 'Erreur interne du serveur' });
  }
});

module.exports = {
  registerUser,
  loginUser,
  getUserProfile,
};
