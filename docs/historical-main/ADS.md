# BRYME Advertising Plan — Monetag

Status: **plan ready, awaiting your Monetag account + zone IDs.** Nothing is
injected anywhere yet — no placeholder ads, no dead scripts.

## Monetag formats (and what they mean for BRYME)

| Format | What it is | Website | Mini App |
|---|---|---|---|
| Popunder (OnClick) | Full-tab ad on click | ⚠️ works but intrusive; **not AdSense-compatible** | ❌ never |
| Push notifications | Browser notifications (needs opt-in + their file on domain) | ✅ works | ❌ no service worker in Telegram webview |
| Vignette banner | Centered native banner w/ Close + CTA | ✅ good, AdSense-compatible | ❌ overlay breaks mini app UX |
| In-Page Push | Native notification-style banner inside the page | ✅ best UX/revenue balance, AdSense-compatible, works on iOS | ⚠️ possible but risky in webview |
| Interstitial | Skippable full-screen on page load, delay configurable | ✅ (use long delay + cap) | ❌ breaks Telegram UX |
| SmartLink (Direct Link) | A plain URL → auto-matched offer. Unlimited per page, allowed on social/redirect/404 traffic | ✅ | ✅ **the only clean mini-app format** |

MultiTag = one script that AI-mixes Popunder + Push + In-Page Push + Interstitial + Vignette.

## Monetag publisher rules (from their policy/reviews)

1. No adult, torrent, or malware content — BRYME is clean ✅
2. Free site builders (Blogspot/Wix) are rejected — BRYME is on Render (real
   cloud hosting) ✅ but final approval is their manual review
3. Native ads must be **clearly labeled** ("Sponsored" / "Ad") — FTC disclosure
4. No deceptive placement (fake buttons, misclick traps)
5. Traffic quality matters: social/Telegram traffic is accepted, bot traffic is banned
6. Min payout $5, paid weekly (Thursdays)

## BRYME placement plan (policy-compliant)

### Website — bryme.onrender.com
- **One In-Page Push zone** in article body mid-scroll (after ~3rd paragraph)
- **One Vignette banner** with frequency cap (1/session) — non-intrusive
- Skip Popunder initially (keeps AdSense compatibility for the future)
- Or start with **one MultiTag** if you prefer max revenue over UX control

### Mini App — labeled Sponsored card only
- The app already has monetization slots built in (`data-monetization-slot`
  hooks: home-top, home-bottom, hub-*-top/bottom, article-top/bottom, cat-*-top).
- Plan: ONE "Sponsored" card on the Mini App home bottom slot + ONE at article
  bottom, both clearly labeled, pointing to a **SmartLink URL**.
- No pop/overlay scripts inside Telegram — protects the clean UX and avoids
  webview rendering problems.

## What you need to do (15 min)

1. Sign up at monetag.com → Add Site → `bryme.onrender.com` → pass review
2. Create zones:
   - Zone A "Website In-Page Push" (or MultiTag) → copy the script snippet
   - Zone B "SmartLink" → copy the direct URL
3. Send me both (the snippet + URL — NOT your account login). I will:
   - website: inject the script via the existing layout (one commit)
   - mini app: wire the labeled Sponsored cards to the SmartLink (gated —
     renders nothing until the URL exists, so no placeholders ever)

## Revenue expectations (honest)

- Nigerian/West-African GEO CPMs are low ($0.1–$1 range for most formats);
- Real money starts with volume: the bot + mini app funnel is the growth lever;
- The verified-markets Money section is a *retention* feature — it grows the
  audience ads monetize. Don't expect ad revenue to lead.
