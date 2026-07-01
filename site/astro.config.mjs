import { defineConfig } from 'astro/config';

// Static site (default output). Deploys to GitHub Pages.
// When the repo + domain are decided, set these:
//   site: 'https://<org>.github.io',
//   base: '/<repo>',            // omit base if using a custom domain at the root
// and run `npm run build` -> output in ./dist
export default defineConfig({
  // Served at the org root (https://toronto-aurora.github.io/), so no `base` is needed
  // and absolute links (/people, /hero/...) work as-is. If a custom domain is added
  // later, just change `site` (still root, no base).
  site: 'https://toronto-aurora.github.io',
  trailingSlash: 'ignore',
});
