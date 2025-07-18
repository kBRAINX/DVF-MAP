const bcrypt = require('bcrypt');

/**
 * Hache un mot de passe
 * @param {string} password - Le mot de passe à hacher
 * @returns {Promise<string>} - Le mot de passe haché
 */
const hashPassword = async (password) => {
  try {
    const saltRounds = 10;
    return await bcrypt.hash(password, saltRounds);
  } catch (error) {
    throw new Error('Erreur lors du hachage du mot de passe');
  }
};

/**
 * Compare un mot de passe avec son hash
 * @param {string} password - Le mot de passe en clair
 * @param {string} hashedPassword - Le mot de passe haché
 * @returns {Promise<boolean>} - True si les mots de passe correspondent
 */
const comparePassword = async (password, hashedPassword) => {
  try {
    return await bcrypt.compare(password, hashedPassword);
  } catch (error) {
    throw new Error('Erreur lors de la comparaison des mots de passe');
  }
};

module.exports = {
  hashPassword,
  comparePassword
};
