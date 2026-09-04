# BRYME website backend (not Telegram)

## What went wrong

The backend in `server/` used to answer **every** request as a Telegram mini-app.

So when that service was pointed at `https://bryme.onrender.com`:

- the home page was the bot, not the website
- Bing and Google got empty or wrong pages
- indexed pages dropped toward zero
- crawl errors piled up

That is a deploy setting, not Bing “breaking.”

## What this backend does now

`node server/server.js` serves **the website first**:

- `/` → the real BRYME homepage
- `/movie/…`, `/sports/…`, `/make-money/…` → normal pages
- duplicate URLs in `_redirects` → **301** (example: `/movie/breaking-bad/` → `/series/breaking-bad/`)
- missing pages → **HTTP 404** with `404.html`
- `/api/search?q=` → catalogue search for the site
- `/healthz` → health check

Telegram is **off** unless you set `TELEGRAM_ENABLED=1`. Even then it only lives at `/telegram/webhook`. It never owns `/`.

## Render (do this)

1. Open the **Web Service** that is attached to this repo.
2. If its name is `bryme-telegram` or the start command is a bot, that is the problem.
3. Settings:
   - **Root Directory:** `server`
   - **Build:** `npm install`
   - **Start:** `node server.js`
   - **Health check:** `/healthz`
   - **TELEGRAM_ENABLED:** `0`
4. Save and deploy.
5. Visit `https://bryme.onrender.com/` — you must see the Movies / Sports / Money homepage, not a Telegram screen.

Keep the **static site** only if this web service is a *different* URL. One public URL. One website.

## Bing / crawl recovery

After the website is the website again:

1. In Bing Webmaster Tools, resubmit `https://bryme.onrender.com/sitemap.xml`
2. Use IndexNow (already in the repo):

```bash
node scripts/indexnow.js --since 2026-08-01 --send
```

3. Wait. Bing will recrawl. Pages do not come back the same day.

## Do not

- Do not deploy a Telegram bot to the same URL as the website.
- Do not set Root Directory to a bot-only folder that does not contain the HTML site.
