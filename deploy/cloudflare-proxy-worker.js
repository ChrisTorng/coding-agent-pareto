/**
 * Coding Agent Pareto static-source proxy. A Cloudflare Worker custom domain
 * serves GHA-generated files committed into public GitHub web/ after CI passes.
 * Domain: https://coding-agent-pareto.christorng.idv.tw/
 * GitHub Pages can replace this proxy after Pages is enabled in repository Settings.
 */
export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname === '/' ? 'index.html' : url.pathname.replace(/^\//, '');
    if (!/^(?:index\.html|app\.js|style\.css|data\.json|charts\/[a-zA-Z0-9_.-]+\.(?:png|svg))$/.test(path)) {
      return new Response('Not found', { status: 404 });
    }
    const source = 'https://raw.githubusercontent.com/ChrisTorng/coding-agent-pareto/main/web/' + path;
    const upstream = await fetch(source, { headers: { Accept: '*/*' } });
    if (!upstream.ok) return new Response('Resource unavailable', { status: upstream.status });
    const ext = path.split('.').pop();
    const types = {html:'text/html; charset=utf-8',js:'application/javascript; charset=utf-8',css:'text/css; charset=utf-8',json:'application/json; charset=utf-8',png:'image/png',svg:'image/svg+xml'};
    const headers = new Headers({
      'Content-Type': types[ext] || 'application/octet-stream',
      'Cache-Control': path === 'data.json' ? 'public, max-age=90' : 'public, max-age=360',
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'SAMEORIGIN'
    });
    return new Response(upstream.body, { status: 200, headers });
  }
};