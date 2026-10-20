import { defineConfig, type Plugin } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// Inline the (small, purged) stylesheet into index.html so first paint doesn't wait on a
// second request. The separate CSS file is dropped from the output.
function inlineCss(): Plugin {
  return {
    name: 'inline-css',
    apply: 'build',
    enforce: 'post',
    transformIndexHtml(html, ctx) {
      const bundle = ctx.bundle;
      if (!bundle) return html;
      return html.replace(/<link rel="stylesheet"[^>]*href="([^"]+)"[^>]*>/g, (tag, href: string) => {
        const key = href.replace(/^\//, '');
        const asset = bundle[key];
        if (!asset || asset.type !== 'asset') return tag;
        delete bundle[key];
        return `<style>${String(asset.source)}</style>`;
      });
    },
  };
}

// Preload the fonts the first screen needs (the latin subsets only), so they arrive with the
// page instead of after the CSS is parsed and text has already been laid out.
const NEWLINE = String.fromCharCode(10);

function preloadFonts(): Plugin {
  const critical = [/geist-latin-wght-normal/, /instrument-serif-latin-400-normal/, /instrument-serif-latin-400-italic/];
  return {
    name: 'preload-fonts',
    apply: 'build',
    enforce: 'post',
    transformIndexHtml(html, ctx) {
      const bundle = ctx.bundle;
      if (!bundle) return html;
      const links = Object.keys(bundle)
        .filter((file) => file.endsWith('.woff2') && critical.some((re) => re.test(file)))
        .map((file) => `<link rel="preload" href="/${file}" as="font" type="font/woff2" crossorigin />`);
      const block = links.map((l) => `    ${l}`).join(NEWLINE);
      return html.replace('</head>', `${block}${NEWLINE}  </head>`);
    },
  };
}

const proxy = {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path: string) => path.replace(/^\/api/, ''),
  },
};

export default defineConfig({
  plugins: [react(), inlineCss(), preloadFonts()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: { proxy },
  // `vite preview` serves the production build; give it the same /api proxy the host
  // (Vercel) provides in production, so the built app can be tested locally.
  preview: { proxy },
});
