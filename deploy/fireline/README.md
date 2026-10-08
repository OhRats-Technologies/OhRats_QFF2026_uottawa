# Fireline hosting

[Fireline](https://fireline.ohrats.party/) · [Presentation](https://fireline.ohrats.party/presentation/)

A static Nginx container serves both from the same domain. Browser calculations, saves and audio need no server-side Python, credentials or QPU access.

The homepage opens the game. `/web/demo/` and `/demo/` redirect there; `/web/presentation/` redirects to `/presentation/`. Shared drawing modules remain under `/demo/canvas/` for the deck’s imports, and map assets keep their relative paths.

Coolify settings:

- Project/environment: OhRats / production, server: localhost.
- Source: existing OhRats GitHub App, `OhRats-Technologies/OhRats_QFF2026_uottawa`, branch `main`.
- Build: Dockerfile, base directory `/`, Dockerfile `/Dockerfile`.
- Exposed container port: `80`; no host port mapping or persistent volume.
- Domain: `https://fireline.ohrats.party`; Cloudflare proxy remains enabled.
- Automatic deployment enabled for GitHub pushes. Health endpoint: `/healthz`.

Only the public game and presentation enter the image. Private research outputs, repository metadata, environment files, tests and build scripts are excluded. The deck includes its committed public evidence and existing PDF/PowerPoint snapshots. Assets use stable names, so responses set `Cache-Control: no-store, max-age=0` and `Cloudflare-CDN-Cache-Control: no-store`. Cloudflare previously raised `max-age=0` to a four-hour browser lifetime; open tabs could keep old modules even after a successful deployment. An existing stale browser cache needs one hard refresh after this correction; game saves remain in local storage.

After each rollout, compare public JS/JSON bytes with the deployed Git commit and confirm the returned cache headers. A healthy container alone does not establish that a browser has fetched the new assets. See [Cloudflare's Browser Cache TTL behavior](https://developers.cloudflare.com/cache/how-to/edge-browser-cache-ttl/) and [origin cache directives](https://developers.cloudflare.com/cache/concepts/cache-control/).

Local container check:

```sh
docker build -t fireline:local .
docker run --rm -p 127.0.0.1:8791:80 fireline:local
```

Check `/`, `/canvas/main.js`, `/canvas/data.json`, `/presentation/`, `/presentation/app.js`, `/demo/canvas/paint.js`, `/presentation/assets/ontario-cover.png`, `/presentation/assets/map.json` and `/healthz`. Verify the deployed container commit and both HTTPS surfaces before declaring a rollout complete. The existing Bun presentation server remains available for local authoring.
