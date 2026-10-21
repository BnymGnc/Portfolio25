// Same-origin cookie proxy. Backend address is server-only; no LLM key here.
export default async function handler(req, res) {
  res.setHeader('Cache-Control', 'private, no-store');
  const origin = process.env.BACKEND_ORIGIN;
  if (!origin || !/^https:\/\/[^/]+\/?$/.test(origin)) {
    return res.status(503).json({detail:'Backend adresi henüz yapılandırılmadı.'});
  }
  const url = new URL(req.url, 'https://local.invalid');
  if (!url.pathname.startsWith('/api/') || !['GET','POST','PUT','HEAD','OPTIONS'].includes(req.method)) {
    return res.status(400).json({detail:'Geçersiz API isteği.'});
  }
  const headers = {};
  for (const key of ['content-type','cookie','origin','x-csrf-token','accept']) {
    if (typeof req.headers[key] === 'string') headers[key] = req.headers[key];
  }
  const body = ['GET','HEAD','OPTIONS'].includes(req.method) ? undefined :
    typeof req.body === 'string' ? req.body : JSON.stringify(req.body ?? {});
  if (body && Buffer.byteLength(body)>2_000_000) return res.status(413).json({detail:'İstek boyutu sınırı aşıldı.'});
  try {
    const upstream = await fetch(origin.replace(/\/$/,'')+url.pathname+url.search, {
      method:req.method, headers, body, redirect:'manual', signal:AbortSignal.timeout(165000)
    });
    // Explicit allowlist: Set-Cookie remains HttpOnly/Secure and has no backend domain.
    for (const key of ['content-type','content-disposition']) {
      if (upstream.headers.has(key)) res.setHeader(key,upstream.headers.get(key));
    }
    const cookies = upstream.headers.getSetCookie();
    if (cookies.length) res.setHeader('Set-Cookie',cookies);
    res.setHeader('Vary','Cookie, Origin');
    const bytes = Buffer.from(await upstream.arrayBuffer());
    return res.status(upstream.status).send(bytes);
  } catch {
    return res.status(503).json({detail:'Backend yanıt vermedi; kaydetmeden önce kayıt durumunu yenileyin.'});
  }
}
