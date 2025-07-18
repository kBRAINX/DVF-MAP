const crypto = require('crypto');

// Générer une clé secrète de 64 bytes (512 bits)
const secret = crypto.randomBytes(64).toString('hex');

console.log('🔑 Votre JWT_SECRET:');
console.log(secret);
console.log('\n📝 Copiez cette ligne dans votre fichier .env:');
console.log(`JWT_SECRET=${secret}`);
console.log('\n⚠️  Gardez cette clé secrète et ne la partagez jamais!');
