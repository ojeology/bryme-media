#!/usr/bin/env python3
"""Wire the BRYME website to the Telegram bot.

Injects a category-specific Telegram CTA card into the site's key hub pages:
  sports hub, make-money hub, tech hub, entertainment hub, movies hub, comics hub.
Links use t.me deep links (https://t.me/<bot>?start=<category>) so the bot
knows what the user wants before they tap.

Config: site.config.json -> "telegramBotUsername" (create with BotFather first).
Idempotent: skips pages already carrying [data-telegram-cta].
Usage: python3 scripts/wire-telegram-ctas.py [--dry]
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--dry" in sys.argv

cfg = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))
BOT = (cfg.get("telegramBotUsername") or "").strip().lstrip("@")
if not BOT:
    print('site.config.json needs "telegramBotUsername" (from BotFather). Nothing injected.')
    sys.exit(0)

CTAS = {
    "sports/index.html": ("⚽", "Get the latest BRYME Sports updates on Telegram.",
                          "sports", "Open BRYME Sports on Telegram"),
    "make-money/index.html": ("💰", "Want more money-making opportunities? Open BRYME on Telegram.",
                              "money", "Open BRYME Money on Telegram"),
    "tech/index.html": ("🤖", "Ask BRYME about the latest AI and tech discoveries.",
                        "tech", "Open BRYME Tech on Telegram"),
    "entertainment/index.html": ("🎬", "Get the latest movies, series and anime on Telegram.",
                                 "entertainment", "Open BRYME Entertainment on Telegram"),
    "movies/index.html": ("🎬", "Get the latest movies, series and anime on Telegram.",
                          "entertainment", "Open BRYME Entertainment on Telegram"),
    "sports/comics/index.html": ("😂", "The weekend's storylines, drawn. Get BRYME comics on Telegram.",
                                 "comics", "Open BRYME Comics on Telegram"),
}

def build_cta(emoji, copy, cat, btn):
    return (
        '<section class="bsd-sec" aria-label="BRYME on Telegram" data-telegram-cta>\n'
        '<div class="bsd-panel" style="padding:18px;display:grid;gap:10px;justify-items:start;'
        'background:linear-gradient(150deg,#101913,#10141b 70%);border-color:#22352a">\n'
        f'<div style="font-size:24px" aria-hidden="true">{emoji}</div>\n'
        f'<p style="margin:0;font-size:15px;font-weight:600;max-width:52ch">{copy}</p>\n'
        f'<a class="bsd-btn bsd-btn-primary" href="https://t.me/{BOT}?start={cat}" target="_blank" rel="noopener">{btn}'
        ' <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></a>\n'
        '</div></section>\n'
    )

def main():
    done, skipped, missing = [], [], []
    for rel, (emoji, copy, cat, btn) in CTAS.items():
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            missing.append(rel)
            continue
        html = open(p, encoding="utf-8").read()
        if "data-telegram-cta" in html:
            skipped.append(rel)
            continue
        # insert before the last closing </main> (inside the page content)
        m = list(re.finditer(r"</main>", html))
        if not m:
            missing.append(rel + " (no </main>)")
            continue
        i = m[-1].start()
        html = html[:i] + build_cta(emoji, copy, cat, btn) + html[i:]
        if not DRY:
            open(p, "w", encoding="utf-8").write(html)
        done.append(rel)
    print("injected:", len(done), done)
    print("already wired (skipped):", len(skipped))
    print("missing:", missing or "none")
    print("dry-run" if DRY else "applied")

if __name__ == "__main__":
    main()
