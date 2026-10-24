// Cloudflare Worker for the static site. Serves the exported pages (site/) and
// receives the consultation form at POST /api/consultation, emailing it through
// Resend. Until RESEND_API_KEY is set, submissions are refused with 503 and the
// page tells visitors to use WhatsApp or phone instead.
//
// Settings (Worker → Settings → Variables and Secrets):
//   RESEND_API_KEY  secret
//   TO_EMAIL        where requests are sent, e.g. the firm's email
//   FROM_EMAIL      a sender on the domain verified in Resend

const LIMITS = { full_name: 120, phone: 30, email: 254, message: 1000, request_type: 40, matter: 40, preferred_contact: 40 };
const LABELS = {
  request_type: 'Request type', full_name: 'Full name', phone: 'Phone', email: 'Email',
  matter: 'Matter', preferred_contact: 'Preferred contact', message: 'Message', language: 'Language',
};

const json = (status, body) => new Response(JSON.stringify(body), {
  status, headers: { 'content-type': 'application/json' },
});

function validate(data) {
  const v = {};
  for (const [key, max] of Object.entries(LIMITS)) {
    v[key] = String(data.get(key) || '').trim().slice(0, max);
  }
  v.full_name = v.full_name.split(/\s+/).join(' ');
  v.language = data.get('language') === 'en' ? 'en' : 'ar';
  const digits = v.phone.replace(/\D/g, '');
  const errors = [];
  if (!v.request_type) errors.push('request_type');
  if (!v.full_name) errors.push('full_name');
  if (!/^\+?[\d\s\-()]+$/.test(v.phone) || digits.length < 7 || digits.length > 15) errors.push('phone');
  if (!v.matter) errors.push('matter');
  if (v.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.email)) errors.push('email');
  if (v.preferred_contact === 'email' && !v.email) errors.push('email');
  if (!data.get('consent')) errors.push('consent');
  return { values: v, errors };
}

async function handleConsultation(request, env) {
  if (request.method !== 'POST') return json(405, { error: 'method' });
  const data = await request.formData();
  if (data.get('website')) return json(200, { ok: true }); // honeypot: pretend success to bots

  const { values, errors } = validate(data);
  if (errors.length) return json(400, { error: 'invalid', fields: errors });
  if (!env.RESEND_API_KEY || !env.TO_EMAIL || !env.FROM_EMAIL) return json(503, { error: 'not_configured' });

  const text = Object.entries(LABELS).map(([k, label]) => `${label}: ${values[k] || '-'}`).join('\n');
  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, 'content-type': 'application/json' },
    body: JSON.stringify({
      from: env.FROM_EMAIL,
      to: [env.TO_EMAIL],
      reply_to: values.email || undefined,
      subject: `Website request: ${values.full_name}`,
      text, // plain text only, so visitor input cannot inject markup
    }),
  });
  return res.ok ? json(200, { ok: true }) : json(502, { error: 'send_failed' });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/api/consultation') return handleConsultation(request, env);
    return env.ASSETS.fetch(request);
  },
};
