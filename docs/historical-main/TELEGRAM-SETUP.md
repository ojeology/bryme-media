# BRYME Telegram Bot + Mini App — setup & operations

The full flow: **Telegram bot → backend API → Mini App deep links → BRYME content**,
all from one content source (`content/posts-index.json`, rebuilt from the same
files the website renders).

**Your frontend is never touched.** The static site (`bryme.onrender.com`) and
the backend are two independent Render services. Creating the backend cannot
modify, replace or break the static site — it simply ignores the `server/` folder.

## 0. Where does the Mini App live? Two supported modes

**Mode A — Mini App hosted on your EXISTING frontend (recommended).**
The Mini App files (`miniapp/`) are part of the repo, so the static site already
serves them at **`https://bryme.onrender.com/miniapp/`** — zero changes to the
frontend. The backend just powers it:

- service env: `MINI_APP_URL=https://bryme.onrender.com/miniapp`
- service env: `API_PUBLIC_URL=https://YOUR-BACKEND.onrender.com`
- BotFather → Web App URL: `https://bryme.onrender.com/miniapp`

The bot automatically appends `?api=<backend>` to every button URL, so the
frontend-hosted Mini App knows where the API is (CORS is enabled on the backend).
If the backend sleeps (free tier), only Telegram features pause — your website
is unaffected.

**Mode B — Mini App hosted by the backend service.**
Set `MINI_APP_URL=https://YOUR-BACKEND.onrender.com` and leave `API_PUBLIC_URL`
unset; the app uses same-origin API calls. Fine for testing, but then the Mini
App shares the backend's free-tier sleep.

**Optional: same-domain `/api` on the frontend.** If you ever want
`bryme.onrender.com/api/*` to proxy the backend, add this to a root `render.yaml`
and sync it as a Blueprint (only if you want it — the static site keeps working
without it):

```yaml
services:
  - type: web
    name: bryme
    runtime: static
    buildCommand: ""
    staticPublishPath: .
    routes:
      - type: proxy
        source: /api/*
        destination: https://YOUR-BACKEND.onrender.com/api/:splat
  - type: web
    name: bryme-telegram
    runtime: node
    rootDir: server
    plan: free
    startCommand: node server.js
    healthCheckPath: /healthz
```

```
BRYME content (JSON + HTML)  ──scripts/build-posts-index.js──▶  content/posts-index.json
                                                                      │
                                                       server/server.js (Render web service)
                                                       ├── GET /api/posts/latest
                                                       ├── GET /api/posts/category/:cat
                                                       ├── GET /api/posts/:slug
                                                       ├── POST /telegram/webhook  (bot logic)
                                                       └── (Mode B only) serves miniapp/
```

## 1. Create the bot (BotFather, ~2 minutes)

1. In Telegram, open **@BotFather** → `/newbot` → name it (e.g. `BRYME`), pick a username (e.g. `bryme_discovery_bot`).
2. Copy the **bot token** → service env var `TELEGRAM_BOT_TOKEN`.
3. **Attach the Mini App URL**: BotFather → `/mybots` → your bot → *Bot Settings* → *Menu Button* → set URL to `https://bryme.onrender.com/miniapp` (Mode A) and text `BRYME`.
4. (Recommended) Also *Bot Settings → Web App URL* — same value, so `web_app` buttons work everywhere.
5. Put the username (without @) into `site.config.json` → `"telegramBotUsername"`, then run:
   `python3 scripts/wire-telegram-ctas.py` to add the website → bot links.

## 2. Deploy the backend (Render) — does NOT touch the frontend

- New **Web Service** from this repo, **Root Directory: `server`**, Start: `node server.js`, health check `/healthz`. (Blueprint provided at `server/render.yaml`.)
- Env vars:
  | var | required | notes |
  |---|---|---|
  | `TELEGRAM_BOT_TOKEN` | yes | from BotFather, secret |
  | `TELEGRAM_WEBHOOK_SECRET` | recommended | random string; setup tool generates one |
  | `MINI_APP_URL` | yes | Mode A: `https://bryme.onrender.com/miniapp` |
  | `API_PUBLIC_URL` | Mode A | `https://YOUR-BACKEND.onrender.com` |
- Free plan is fine; the service is stateless.

## 3. Register the webhook (one command)

```
TELEGRAM_BOT_TOKEN=... node scripts/setup-telegram.js --set-webhook https://YOUR-BACKEND.onrender.com
TELEGRAM_BOT_TOKEN=... node scripts/setup-telegram.js --set-menu-button https://bryme.onrender.com/miniapp
```

The tool prints the generated `TELEGRAM_WEBHOOK_SECRET` — add it to the service env and redeploy.

## 4. Publishing content (single source of truth)

After publishing/changing articles on the site, rebuild the index and deploy:

```
node scripts/build-posts-index.js     # regenerates content/posts-index.json + posts-bodies.json
git add content/posts-index.json content/posts-bodies.json && git commit -m "content: refresh index" && git push
```

Render redeploys the service; the bot and Mini App serve the new content immediately
(the server re-reads the files by mtime — no restart needed if you edit them in place).

## 5. Verify the flow

- `GET /healthz` → `{"ok":true,"posts":N}`
- `GET /api/posts/latest?limit=5` → published posts only
- `GET /api/posts/category/money` → money posts
- `GET /api/posts/<slug>` → full article incl. body; unknown slug → 404 JSON with fallback route
- Telegram: `/start` → menu; tap 💰 Make Money → snippet + *Open in BRYME*; 🆕 Latest Posts → list of article buttons; `t.me/<bot>?start=sports` from the website → straight to Sports.

## Security notes

- The bot token lives only in env vars; the webhook rejects requests without the secret header.
- Only **published** content is indexed. Drafts (`status != "published"`) never reach Telegram.
- The Mini App works in a plain browser too (Telegram SDK is optional at runtime) — safe for dev.
