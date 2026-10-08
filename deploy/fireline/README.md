# Fireline hosting

Fireline is served at https://fireline.ohrats.party/ by a static Nginx container. The browser presentation is at https://fireline.ohrats.party/presentation/. Browser calculations, saves and audio need no backend, Python, credentials or QPU access. The root opens the game; `/web/demo/` and `/demo/` redirect to it. `/web/presentation/` redirects to the deck. Shared game drawing modules remain available below `/demo/canvas/` for the presentation's imports. The Ontario cover image and map metadata retain the relative paths used by the game asset loader.

Coolify settings:

- Project/environment: OhRats / production, server: localhost.
- Source: existing OhRats GitHub App, `OhRats-Technologies/OhRats_QFF2026_uottawa`, branch `main`.
- Build: Dockerfile, base directory `/`, Dockerfile `/Dockerfile`.
- Exposed container port: `80`; no host port mapping or persistent volume.
- Domain: `https://fireline.ohrats.party`; Cloudflare proxy remains enabled.
- Automatic deployment enabled for GitHub pushes. Health endpoint: `/healthz`.

Only the public game and presentation enter the image. Private research outputs, repository metadata, environment files, tests and build scripts are excluded. The deck includes its committed public evidence and existing PDF/PowerPoint snapshots. Assets currently use stable names, so responses revalidate rather than claiming immutable caching.

Local container check:

```sh
docker build -t fireline:local .
docker run --rm -p 127.0.0.1:8791:80 fireline:local
```

Check `/`, `/canvas/main.js`, `/canvas/data.json`, `/presentation/`, `/presentation/app.js`, `/demo/canvas/paint.js`, `/presentation/assets/ontario-cover.png`, `/presentation/assets/map.json` and `/healthz`. Verify the deployed container commit and both HTTPS surfaces before declaring a rollout complete. The existing Bun presentation server remains available for local authoring.
