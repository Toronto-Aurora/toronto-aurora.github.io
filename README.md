# Aurora Institute — website

Static site for the Aurora Institute (working name), a cross-institutional high-z research initiative of the University of Toronto and York University. Built with [Astro](https://astro.build), deploys to GitHub Pages.

See `STRATEGY.md` (in this folder) for the full design and content strategy and the peer-institute benchmark behind it.

## Structure

```
site/
  astro.config.mjs        # build config (set site/base before GitHub Pages deploy)
  src/
    layouts/Base.astro     # shared <head>, nav, footer, fonts
    components/            # Logo, Nav, Footer
    pages/                 # index (home, single scroll), people, programs, news
    data/                  # EDIT THESE: team, news, fellowships, collaborators (JSON)
    styles/global.css      # brand tokens + all styles
  public/favicon.svg
```

## Run locally

```
cd site
npm install        # first time only
npm run dev        # http://localhost:4321
```

Note: the in-app preview helper cannot `chdir` into Dropbox CloudStorage paths (macOS sandbox), so it serves a built snapshot from a scratch dir instead. A normal terminal (`npm run dev`) works fine.

## Build

```
cd site
npm run build      # outputs static files to site/dist/
npm run preview    # serve the production build locally
```

## Deploy to GitHub Pages

1. Push `site/` to a repo (or move it to the repo root).
2. In `astro.config.mjs`, set `site` and, for a project page, `base: '/<repo>'`. For a custom domain at the root, set `site: 'https://aurorainstitute.ca'` and leave `base` unset.
3. Add a GitHub Actions workflow (Astro's official `withastro/action`) or push `dist/` to the `gh-pages` branch.
4. For a custom domain, add a `CNAME` file in `public/` and point DNS at GitHub Pages.

## Status of content

Done (verified):
- Front page hero: a full-width three-panel showcase (`components/Hero.astro`). Observation = crossfading JWST/ALMA images (`public/hero/obs/`, public domain / CC, credited on-panel). Theory = two real simulation videos (`public/hero/theory/`): THESAN reionization of the cosmic web and a THESAN-ZOOM high-redshift galaxy forming through mergers and feedback, both THESAN / THESAN-ZOOM Simulations under CC BY 4.0, credited on-panel (THESAN is co-led by member R. Kannan, so the team can also request bespoke frames). Data science = an interactive "connecting dots" canvas that links points near the cursor. To swap any visual, replace the files in `public/hero/...` and the lists at the top of `Hero.astro`.
- `src/data/team.json`: affiliations and one-line foci verified from each member's official page. Each member has a verified personal/faculty link. TBC items resolved: A. Sajina is at Tufts and U.-L. Pen is ASIAA-primary (both shown as external-affiliated associates — confirm placement); A. Levis is Computer Science (astro cross-appointment).
- `src/data/news.json`: four recent member preprints with arXiv links, each verified to resolve.
- `src/data/collaborators.json`: a 14-city draft network based on members' collaborations.
- `src/data/fellowships.json`: from the vision doc; verified links.
- Contact: interim `seiji.fujimoto@utoronto.ca` (in `Footer.astro` and `programs.astro`). Switch to `info@aurorainstitute.ca` once the domain is registered.
- Visitor program: concrete pilot terms (draft, pending Dunlap Blue-Sky funding) on `programs.astro`.

Still to do:
- Headshots: currently hotlinked from official pages with a graceful fallback to initials. For production, download them to `public/people/` (with each member's consent) and point `photo` at the local path. A few members have no public headshot yet (initials shown).
- Hero image / clip: still the SVG aurora motif. Replace with a VENUS image or short clip (our own imagery, not NASA stock).
- News: curate and add institute news (fellow arrivals, talks, awards) as Aurora launches.
- Collaborator map: confirm/curate the real partner list; optionally upgrade the static SVG map to Leaflet + OpenStreetMap.
- Domain: staying on `*.github.io` for now. `aurorainstitute.ca` and `aurora-institute.ca` are available if/when you want a custom domain. Note: `aurora-institute.org` belongs to a US education nonprofit (now redirecting to Full Scale Learning), so the name collides in web search but not in astronomy.
- Logo: concept 1 ("Aurora curtain A") in `components/Logo.astro` and `public/favicon.svg`. Swap when the final mark is chosen.

## Upgrade paths (deferred)

- Interactive collaborator map: swap the static SVG in `index.astro` for Leaflet + OpenStreetMap (no API key) fed by `collaborators.json`.
- Full-text search: add Pagefind at build time.
- Contact form: Formspree, or a small endpoint on the existing VM.
- Anything dynamic or gated (student portal, live data): host on the existing VM under a subdomain; keep the public site on GitHub Pages.
