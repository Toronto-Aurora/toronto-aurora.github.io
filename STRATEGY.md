# Aurora Initiative — Website Strategy and Design Plan

Working draft v0.1 (2026-06-30). Author: Seiji + Claude. Audience: Aurora coordinators (Fujimoto, Dayal, Muzzin, Speagle) and the student developer.

This document is grounded in two inputs: (1) the team vision statement and meeting minutes in the shared Google Doc, and (2) a benchmark of seven peer institute websites (DAWN, Cosmic Frontier Center, Kavli IPMU, Flatiron CCA, ICRAR, MPA Garching, Dunlap) plus published guidance on academic recruiting sites. Every peer claim below comes from pages fetched during that benchmark.

---

## 1. Purpose and phase

We are in a visibility-building phase, not a transactional phase. The site's job is to make the global high-z community feel that Toronto has momentum, a distinctive approach, and concrete things to offer early-career people, so that strong postdocs and students choose to bring their fellowships here or to visit. The site is the front door for that. It is not primarily an internal tool.

Concretely, the site should move three audiences:
- Prospective postdocs and PhD students deciding where to apply or where to bring an external fellowship.
- International collaborators deciding whether to visit or partner.
- Funders and senior peers forming an impression of whether Aurora is real and rising.

## 2. What the site must achieve (success criteria)

1. A visitor understands within ten seconds that Aurora studies the first billion years and that its edge is the integration of observation, theory, and data science.
2. A prospective fellow can find, in one click, exactly what Aurora offers them (co-mentorship, fellowship extension, visitor program, career support) with concrete terms, not slogans.
3. The site reads as active and rising, with dated activity, named people with photos, and real projects, rather than a static "we exist" page.
4. The cross-institution model (UofT and York) reads as a feature, with people from both sites shown together.
5. It looks polished on a phone and loads fast. First impressions are the whole point in this phase; a half-built or stale page does as much damage as no page.

## 3. Positioning: one story, three proof pillars

The single most repeated lesson from the benchmark: lead with the science question in plain language, not with institutional self-description. CFC Austin uses one concrete claim ("the most distant black hole ever confirmed") as its hook. Flatiron CCA opens with what it does and why it matters. The weak examples open with geography or with a list of institutional attributes.

Proposed hero line (plain English, swappable):
> Aurora studies how the first galaxies and black holes formed in the universe's first billion years, and how they reshaped the cosmos around them.

Supporting line that states the edge:
> We are built to do this across observation, theory, and data science at once, which most groups cannot.

Three proof pillars, each anchored by a named person and a real example, not an abstract topic:
- Observation: JWST large programs defining the high-z frontier (for example VENUS, plus GTO and treasury surveys at UofT and York).
- Theory and simulation: CITA and the York computational group (radiation hydro, reionization, galaxy and seed-black-hole formation).
- Data science: joint appointments between Statistical Sciences and DADDAA (Bayesian inference, ML, survey methodology), with the Vector Institute and DSI ecosystem adjacent.

A flagship result in the hero (for example a VENUS or GNz7q image and one sentence) does more than three abstract topic words. Use Aurora's own imagery, not NASA stock (per the team's meeting feedback).

## 4. Peer benchmark: what to copy, what to avoid

| Institute | Signature move | Take for Aurora |
|---|---|---|
| Cosmic Dawn Center (cosmicdawn.dk) | Standalone domain separate from the university CMS; public JWST data archive (DJA); people directory with role filters; high-volume dated news; postdocs visibly mentor students | Own domain, not a department subpage. Own one public resource. Make postdoc-led mentoring a named feature. |
| Cosmic Frontier Center (UT Austin) | Director pair (observer Finkelstein + theorist Bromm) as the institutional face; one flagship discovery as hook; named Prize Fellows | Anchor pillars with named humans. Lead with one result. But note: CFC lives inside the dept site and several subpages 404. Avoid that; be standalone and complete. |
| Kavli IPMU | People directory with 10 categories including Visitors and Joint Appointments; prize announcements as the momentum feed; EN/JP toggle | Make visitors and cross-institution joint mentoring visible in the directory itself. Use awards as recurring news. |
| Flatiron CCA | Verbatim mission with five numbered goals (one is explicitly about training early-career people); named open-source software directory; "Learning the Universe" multi-institution showcase with partner logos; fully funded, no grant-writing pitch | Publish a short numbered mission that names co-mentorship and extension. Build a "Data and tools" identity. Show UofT and York as a named network with logos and faces. |
| ICRAR | Visiting fellowship page with concrete terms: duration, stipend, travel and needs-based support, eligibility, application window; childcare/equity funding named | Give the visitor program its own page with real numbers and dates, not "coming soon". |
| MPA Garching | "MPA Fellows" as an editorial news category (every fellow generates ongoing content); live events calendar; ERC/prize wins dated on the homepage | Treat each fellow arrival, first paper, and placement as a dated news item. Show a seminar/workshop calendar. |
| Dunlap (UofT) | "From Fellow to Faculty" career-trajectory framing; culture/climate transparency; SURP undergrad pipeline | Make the career-trajectory claim explicit. Link to Dunlap's existing career and visitor activities rather than duplicating them. |

Recurring patterns across all seven, in priority order:
1. Standalone domain and a complete, non-broken site beats a department subpage.
2. Hero leads with the science question in plain language, plus one flagship result.
3. "Join / Opportunities" is one click from anywhere and full of specifics.
4. The people page is the most-visited page for recruitment. Photos, roles, one-sentence research focus, and an alumni tracker matter more than prose.
5. A dated activity feed is the single clearest momentum signal. Continuous low-hum beats rare big announcements.
6. Name concrete infrastructure: telescope programs, compute, travel funding, seminars.
7. Own one public open resource (data or code) to read as infrastructure, not just a label.
8. For a new institute, frame the newness as an asset ("shape an institute from the ground up") with a dated roadmap.

## 5. Information architecture (site map)

Single-page scroll for the home view (per team feedback: tabs scroll to anchored sections), with a small number of deeper standalone pages for the content that needs depth and stable URLs (people, the programs/join page, news archive). This hybrid gives the polished scroll experience while keeping the recruitment-critical content on real, linkable, complete pages.

```
Home (single scroll, sticky anchor nav)
  Hero            our own image + one-line science story + 3 pillars + CTAs (Join / Visit)
  What we offer   4 clickable cards: co-mentorship | +1yr extension | visitor program | career
  Science         the three questions, each with a named pillar lead and a real example
  Network         UofT + York shown together; collaborator world map; partner logos
  Momentum        latest dated news / preprints / talks (pulls from the news page)
  Footer          contact, social, land acknowledgment, institution logos

Standalone pages (in the top nav, always resolve)
  People          tree: Coordinators -> Core faculty -> Associates; photos, role, 1-line focus,
                  personal-site links; co-mentors shown together; Visitors tab; Alumni tracker
  Programs / Join the offer in full: co-mentorship explained, extension terms + eligible
                  fellowships (the country list from the vision doc), visitor tracks with
                  concrete terms, how to apply, who to contact, prize-fellowship hosting
  News            dated archive (discoveries, fellow arrivals, awards, talks)
  Science (opt.)  deeper project pages if/when individual projects want a home

Later / optional
  Data & tools    a public Aurora resource (data product or code) when ready
  Internal        password-gated team area (move to the VM if/when needed)
```

Top nav labels (from the team's layout slide, lightly adjusted): Home · Science · People · Programs · News · Join us.

## 6. Front page blueprint, section by section

1. Sticky nav: small Aurora mark + wordmark on the left; anchor links on the right; a single accent "Join us" button. Active-section highlight as you scroll (IntersectionObserver, no library).
2. Hero: full-bleed Aurora/VENUS image or a short looping clip that visually suggests the obs-theory-data synergy. Big wordmark, the one-line science story, the edge line, three pillar chips, and two CTAs (Join us, Visit). Keep the join CTA visible without scrolling on mobile.
3. What we offer: four cards, each with an icon, a two-word title, one line, and a click-through to the Programs page. This is the differentiator and the team's stated priority; it sits immediately under the hero. Co-mentorship uses the two-way-arrow icon the team asked for.
4. Science: the three questions, each as a short block with a named pillar lead, a one-line plain-English statement, and a real example or image. Avoid three abstract topic words.
5. Network: one line on the UofT + York model, partner logos, and the collaborator world map (Leaflet + OpenStreetMap, fed by a JSON file). The map is Seiji's idea and reads instantly as reach.
6. Momentum: three to five most recent dated items pulled from the News page.
7. Footer: contact, social handles (include Bluesky, where the astro community now is), institution logos, land acknowledgment.

Design language: dark "cosmic dawn" hero, lighter body for readability, one aurora-derived accent gradient used sparingly, large type (the team explicitly asked for bigger text), generous spacing, real photos. Modern and editorial, closer to Flatiron CCA than to a default WordPress theme.

## 7. The "what we offer" system (the core differentiator)

This is where Aurora wins or loses the recruitment story, so each item gets a concrete, named treatment on the Programs page, not a slogan.

- Co-mentorship. State what it means in practice: every trainee has at least two mentors from different pillars; joint supervision; shared authorship norms; co-mentored trainees presenting at major meetings. Frame postdoc-led mentoring of students as a feature (DAWN does this well).
- Fellowship extension (+1 year). This is the headline perk and should read as a concrete advantage with a number and a reason, in the manner of the Heising-Simons Astronova ("4+1") and MPIA APEx ("3+1") listings: "Many competitive fellowships run two years. Aurora adds a funded third year to fellows who join, because building an independent research identity takes time, and to make Toronto competitive with longer offers elsewhere." List the eligible awards (UofT A&S, Schmidt AI, DSI, Research Excellence; international: Rubicon, JSPS, Marie Curie, SNSF Mobility, UKRI, Humboldt, CSC, NRF, NSTC, A*STAR, SERB/ANRF). The vision doc already has the URLs; turn that into a public, regularly updated fellowship guide by country. This guide is itself a recruitment magnet.
- Visitor program. Give it concrete, tiered terms (ICRAR model): a short senior-collaborator visit (about two weeks), a summer program for graduate students (longer, with a stipend), and a semester-style embedded postdoc visit. State stipend, duration, eligibility, and the application window. Tie in the existing Dunlap and CITA visitor programs and the CITA MoU rather than duplicating them, and flag Aurora's own program as in preparation with a dated roadmap.
- Career development. Link to Dunlap's existing activities rather than building new ones now, and state the career-trajectory claim plainly (placement outcomes as they accumulate).

## 8. People and co-mentorship presentation

The people page is the highest-leverage recruitment surface. Build it as the team asked, as a tree: Coordinators (Fujimoto, Dayal, Muzzin, Speagle) -> Core faculty -> Associates, with Peter Martin added under theory. Each card: photo, role, one-sentence research focus, institution (UofT or York), and a personal-site link. Show co-mentors together so the cross-pillar, cross-institution model is visible at a glance. Add a Visitors tab and an Alumni tracker early; even one alumnus going to a named position is worth displaying, since "where did people end up" is the question applicants most want answered.

## 9. Momentum engine

Stand up a dated activity feed from day one and post at a steady cadence, even when items are small: new preprints with arXiv links and one-line plain-English summaries, upcoming and recent talks, awards and grants, new arrivals, conference participation. Volume of dated entries is what separates a rising institute from a nameplate. arXiv author feeds and ADS can populate much of this semi-automatically.

## 10. Infrastructure recommendation

Recommended baseline: a standalone static site on GitHub Pages with a custom domain, keeping the existing VM only for anything that genuinely needs a server later. Rationale: in this visibility phase the priorities are a polished first impression, global reach, and near-zero maintenance. GitHub Pages gives a CDN, automatic HTTPS, a custom domain, free hosting, and Git-based collaboration and history. A single-region VM adds latency for overseas visitors and ongoing maintenance for no current benefit. Everything the home, people, programs, news, fellowship guide, and collaborator map need can be done statically. Move to the VM (which already runs the MSA Hub on nginx/systemd) only when a real dynamic need appears (a gated student portal, server-side forms, live data), via a subdomain split.

Static-site framework: one real fork, decided by who maintains the site.
- If a committed student developer (or Claude) owns the build, choose Astro. It gives full control over a bespoke, striking front page, ships almost no JavaScript by default (fast), and still keeps team, news, and programs content as Markdown files that non-developers can edit through the GitHub web UI or pull requests. Best fit for the "distinctive front page" the team wants. The cost is that there is no ready-made academic template, so the design is built once from scratch.
- If the site must be faculty-self-serve with minimal developer involvement, choose Hugo with the HugoBlox academic theme. It ships people, publications, and project sections out of the box, imports publications from BibTeX/ORCID/Zotero automatically, and builds fast. The cost is a more templated look that is harder to make truly bespoke.

Recommendation: Astro, assuming the student developer stays involved, because the front page is the whole game in this phase and Aurora is a virtual institute that does not need an auto-generated group publication list. HugoBlox is the safe fallback if maintenance must be hands-off.

Supporting pieces (all static, no server):
- Domain: register a dedicated domain (for example aurorainstitute.ca, pending name confirmation and availability) rather than a UofT subpath, so links always resolve and branding is independent. A UofT or Dunlap subdomain can redirect to it.
- Collaborator map: Leaflet + OpenStreetMap, fed by a collaborators.json (name, institution, lat/lon, link). No API key, no cost, privacy-respecting. MapLibre is the later upgrade if a styled dark basemap is wanted.
- Search: Pagefind (static full-text search, tiny payload) if/when the site grows enough to need it.
- Contact form: Formspree free tier, or a small endpoint on the existing VM if server-side handling is preferred.
- Single-page scroll with sticky anchor nav and active-section highlight: native CSS sticky plus an IntersectionObserver, no framework lock-in.

## 11. Logo and brand direction

Six concept directions were drafted (shown in chat). They share an aurora visual language that ties "cosmic dawn" to Canada. Shortlist for development:
- Concept 4 (three-strand braid converging to first light): most directly states the three-pillar synergy, which is Aurora's stated edge.
- Concept 1 (aurora curtain forming an "A") and Concept 2 (two crossing auroras): strongest as compact, scalable brand marks; Concept 2 matches Seiji's "two auroras intersecting to harmonize the institutes" idea.

Suggested next step: pick one or two directions, then produce a clean lockup set (horizontal, stacked, icon-only, favicon, and a one-color version) plus a small color and type system that the site inherits. Abstract aurora marks (1, 2, 4, 6) pair better with real VENUS imagery in the hero than the more literal skyline mark (5).

## 12. Build plan (phased)

Phase 0, alignment (now): confirm name, pick logo direction, confirm infra choice, confirm maintenance owner, decide domain. This document plus the logo concepts are the input.
Phase 1, design: a front-page wireframe and a visual comp, plus the site map and content checklist. Iterate with the team before any production build.
Phase 2, content collection: hero image(s) from VENUS, member photos and one-line bios and links, the fellowship guide list (already in the vision doc), initial news items.
Phase 3, build: scaffold the chosen stack, implement the home scroll, people tree, programs/join page, news, and map. Mobile and performance pass.
Phase 4, soft launch: review on phones, fix, then announce. Do not launch until it looks polished (the team's own standard).
Phase 5, momentum: keep the news feed and people/alumni pages current; add the public data/tools resource when ready.

## 13. Open decisions

1. Name: proceed with "Aurora Initiative" as the working brand? (The vision doc has largely converged on it.)
2. Logo: which one or two directions to develop?
3. Infrastructure: accept the GitHub Pages + static baseline? Astro or HugoBlox?
4. Maintenance owner: is there a committed student developer, and should Claude build the first version for them to inherit, or build alongside them?
5. Domain: a dedicated .ca domain, or a UofT/Dunlap subdomain (with redirect)?
6. Content: who supplies hero imagery, member photos, and bios, Claude or the team?
7. Scope of v1: home + people + programs/join + news as the launch set, with the data/tools resource deferred?
