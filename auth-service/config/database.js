const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST,
  port: process.env.DB_PORT,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Test de connexion
pool.on('connect', () => {
  console.log('Connexion à la base de données établie');
});

pool.on('error', (err) => {
  console.error('Erreur de connexion à la base de données:', err);
  process.exit(-1);
});

// Fonction pour tester la connexion
const testConnection = async () => {
  try {
    const client = await pool.connect();
    console.log('Test de connexion à la base de données réussi');
    client.release();
  } catch (err) {
    console.error('Erreur lors du test de connexion:', err);
  }
};

// Tester la connexion au démarrage
testConnection();

module.exports = pool;
