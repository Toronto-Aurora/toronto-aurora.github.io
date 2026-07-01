import { defineConfig } from 'astro/config';

// Static site (default output). Deploys to GitHub Pages.
// When the repo + domain are decided, set these:
//   site: 'https://<org>.github.io',
//   base: '/<repo>',            // omit base if using a custom domain at the root
// and run `npm run build` -> output in ./dist
export default defineConfig({
  // site: 'https://aurorainstitute.ca',
  trailingSlash: 'ignore',
});
