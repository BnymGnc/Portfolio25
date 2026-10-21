export const PRODUCTION_ORIGIN = 'https://buildingportfolio25.vercel.app';

// An immutable Vercel deployment URL is a different browser Origin. Do not
// broaden the backend allowlist or forward credentials to a different site.
export function requiresProductionOrigin(origin: string) {
  try {
    const url = new URL(origin);
    return url.hostname.endsWith('.vercel.app') && url.origin !== PRODUCTION_ORIGIN;
  } catch { return false; }
}

export class OriginRejectedError extends Error {
  constructor() {
    super('Bu adres üzerinden oturum açılmasına izin verilmiyor. Sabit üretim adresini kullanın.');
    this.name = 'OriginRejectedError';
  }
}
