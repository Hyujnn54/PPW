/**
 * PPW Extension — generator.js
 * Pure functions for password generation and strength scoring.
 * No dependencies — works in both the popup and service worker.
 */

const SETS = {
  uppercase: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
  lowercase: 'abcdefghijklmnopqrstuvwxyz',
  digits:    '0123456789',
  symbols:   '!@#$%^&*()-_=+[]{}|;:,.<>?',
};

/**
 * Generate a cryptographically random password.
 * @param {{ length, uppercase, lowercase, digits, symbols }} opts
 * @returns {string}
 */
export function generatePassword(opts = {}) {
  const {
    length    = 20,
    uppercase = true,
    lowercase = true,
    digits    = true,
    symbols   = true,
  } = opts;

  let charset = '';
  const required = [];

  if (uppercase) { charset += SETS.uppercase; required.push(pick(SETS.uppercase)); }
  if (lowercase) { charset += SETS.lowercase; required.push(pick(SETS.lowercase)); }
  if (digits)    { charset += SETS.digits;    required.push(pick(SETS.digits));    }
  if (symbols)   { charset += SETS.symbols;   required.push(pick(SETS.symbols));   }

  if (!charset) charset = SETS.lowercase + SETS.digits;

  const arr = new Uint32Array(length);
  crypto.getRandomValues(arr);

  const chars = Array.from(arr, n => charset[n % charset.length]);

  // Inject required chars at random positions so policy is always met
  required.forEach((ch, i) => { chars[i % length] = ch; });

  // Shuffle
  for (let i = chars.length - 1; i > 0; i--) {
    const j = Math.floor(crypto.getRandomValues(new Uint32Array(1))[0] / 2 ** 32 * (i + 1));
    [chars[i], chars[j]] = [chars[j], chars[i]];
  }

  return chars.join('');
}

/**
 * Score password strength 0–100.
 */
export function strengthScore(pw) {
  if (!pw) return 0;
  let score = 0;

  // Length
  if (pw.length >= 8)  score += 10;
  if (pw.length >= 12) score += 15;
  if (pw.length >= 16) score += 15;
  if (pw.length >= 24) score += 10;

  // Charset variety
  if (/[a-z]/.test(pw))          score += 10;
  if (/[A-Z]/.test(pw))          score += 10;
  if (/[0-9]/.test(pw))          score += 10;
  if (/[^a-zA-Z0-9]/.test(pw))   score += 15;

  // Penalise repetition / sequences
  if (/(.)\1{2,}/.test(pw))      score -= 15;
  if (/(?:abc|123|qwerty)/i.test(pw)) score -= 10;

  return Math.max(0, Math.min(100, score));
}

function pick(charset) {
  return charset[Math.floor(crypto.getRandomValues(new Uint32Array(1))[0] / 2 ** 32 * charset.length)];
}

