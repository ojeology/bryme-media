/* BRYME website backend — zero-dependency Node service.
 *
 * THIS SERVICE SERVES THE PUBLIC WEBSITE FIRST.
 * Telegram is optional and never owns "/" — that is what dropped Bing.
 *
 *   • static website from the repo root (index.html, /movie, /sports, …)
 *   • 301s from _redirects (so /movie/breaking-bad → /series/breaking-bad)
 *   • real HTTP 404 (not a 200 soft-404)
 *   • content APIs the website can call
 *
 * Run:  PORT=8787 node server/server.js
 * Env:  TELEGRAM_ENABLED=1 to attach the bot webhook at /telegram/webhook only
 */
"use strict";

const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const MINIAPP_DIR = path.join(ROOT, "miniapp");
const PORT = Number(process.env.PORT || 8787);
const TOKEN = process.env.TELEGRAM_BOT_TOKEN || "";
const SECRET = process.env.TELEGRAM_WEBHOOK_SECRET || "";
const API_BASE = process.env.TELEGRAM_API_BASE || "https://api.telegram.org";
const MINI_APP_URL = process.env.MINI_APP_URL || "";

const { createBot } = require("./bot");
const API_PUBLIC_URL = process.env.API_PUBLIC_URL || "";

/* ---------- content cache (mtime-refreshed) ---------- */
const INDEX_PATH = path.join(ROOT, "content", "posts-index.json");
const BODIES_PATH = path.join(ROOT, "content", "posts-bodies.json");
let cache = { posts: [], bodies: {}, mtime: 0, bodiesMtime: 0 };

function loadContent() {
  try {
    const m = fs.statSync(INDEX_PATH).mtimeMs;
    const bm = fs.statSync(BODIES_PATH).mtimeMs;
    if (m !== cache.mtime) {
      const idx = JSON.parse(fs.readFileSync(INDEX_PATH, "utf8"));
      cache = { posts: idx.posts || [], bodies: cache.bodies, mtime: m, bodiesMtime: cache.bodiesMtime, builtAt: idx.builtAt };
    }
    if (bm !== cache.bodiesMtime) {
      cache.bodies = JSON.parse(fs.readFileSync(BODIES_PATH, "utf8"));
      cache.bodiesMtime = bm;
    }
  } catch (e) {
    /* keep last good cache */
  }
  return cache;
}

/* ---------- sports competitions cache (mtime-refreshed) ---------- */
/* deploy-tick 9ccdab0+ */
const COMPETITIONS_PATH = path.join(ROOT, "content", "competitions.json");
let ccache = { data: null, mtime: 0 };
function loadCompetitions() {
  try {
    const m = fs.statSync(COMPETITIONS_PATH).mtimeMs;
    if (m !== ccache.mtime || !ccache.data) {
      ccache = { data: JSON.parse(fs.readFileSync(COMPETITIONS_PATH, "utf8")), mtime: m };
    }
  } catch (e) { /* keep last good */ }
  return ccache.data;
}

/* ---------- money opportunities cache (mtime-refreshed) ---------- */
const OPPORTUNITIES_PATH = path.join(ROOT, "content", "opportunities.json");
let ocache = { data: null, mtime: 0 };
function loadOpportunities() {
  try {
    const m = fs.statSync(OPPORTUNITIES_PATH).mtimeMs;
    if (m !== ocache.mtime || !ocache.data) {
      ocache = { data: JSON.parse(fs.readFileSync(OPPORTUNITIES_PATH, "utf8")), mtime: m };
    }
  } catch (e) { /* keep last good */ }
  return ocache.data;
}
const FX = { USD: 1, NGN: 1 / 1500, GBP: 1.27, EUR: 1.09, CAD: 0.73, ZAR: 0.055, KES: 0.0077 };
function usdEq(pay) {
  if (!pay) return 0;
  return Math.max(Number(pay.amountMin) || 0, Number(pay.amountMax) || 0) * (FX[pay.currency] || 1);
}

/* ---------- optional sports data watchdog ----------
 * Production serving is read-only by default. Set WATCHDOG=on only on a
 * writable worker intentionally allowed to refresh source data; normal web
 * deployments consume the GitHub-workflow-validated JSON committed to main. */
const { spawn } = require("child_process");
let refreshing = false;
function competitionsAgeMin() {
  try { return (Date.now() - fs.statSync(COMPETITIONS_PATH).mtimeMs) / 60000; }
  catch (e) { return Infinity; }
}
function refreshCompetitions(reason) {
  if (refreshing) return;
  refreshing = true;
  console.log("[watchdog] refreshing competitions:", reason);
  const p = spawn(process.execPath, [path.join(ROOT, "scripts", "fetch-competitions.js")], { stdio: "ignore" });
  const done = () => { refreshing = false; };
  p.on("exit", done);
  p.on("error", done);
}
function watchdogTick() {
  const age = competitionsAgeMin();
  if (age > 90) refreshCompetitions(Math.round(age) + " min old");
}
if (process.env.WATCHDOG === "on") {
  setInterval(watchdogTick, 30 * 60 * 1000).unref();
  setTimeout(watchdogTick, 45 * 1000).unref(); /* shortly after boot */
}

/* ---------- telegram sender ---------- */
function telegram(method, payload) {
  if (!TOKEN) return Promise.reject(new Error("TELEGRAM_BOT_TOKEN not set"));
  return fetch(API_BASE + "/bot" + TOKEN + "/" + method, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload)
  }).then((r) => r.json());
}

function miniBase(req) {
  if (MINI_APP_URL) return MINI_APP_URL.replace(/\/+$/, "");
  const host = (req.headers["x-forwarded-host"] || req.headers.host || "localhost:" + PORT).split(",")[0].trim();
  const proto = req.headers["x-forwarded-proto"] || (String(host).startsWith("localhost") || String(host).startsWith("127.") ? "http" : "https");
  return proto + "://" + host;
}

function botFor(req) {
  return createBot({
    getPosts: () => loadContent().posts,
    miniAppBase: miniBase(req),
    apiBaseUrl: API_PUBLIC_URL || miniBase(req),
    botUsername: process.env.BOT_USERNAME || "BRYMEHUBBOT",
    getOpportunities: () => {
      const d = loadOpportunities();
      return d ? (d.opportunities || [])
        .filter((o) => o.status === "published" && o.pay)
        .sort((a, b) => usdEq(b.pay) - usdEq(a.pay)) : [];
    },
    send: telegram,
    answerCallback: (id) => telegram("answerCallbackQuery", { callback_query_id: id })
  });
}

/* ---------- helpers ---------- */
const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
  ".xml": "application/xml; charset=utf-8", ".txt": "text/plain; charset=utf-8",
  ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp",
  ".gif": "image/gif", ".svg": "image/svg+xml", ".ico": "image/x-icon",
  ".mp3": "audio/mpeg", ".mp4": "video/mp4", ".webm": "video/webm",
  ".woff2": "font/woff2", ".webmanifest": "application/manifest+json"
};
const TELEGRAM_ON = process.env.TELEGRAM_ENABLED === "1" || process.env.TELEGRAM_ENABLED === "true";
const SECURITY_HEADERS = Object.freeze({
  "content-security-policy": [
    "default-src 'self'",
    "base-uri 'self'",
    "object-src 'none'",
    "form-action 'self'",
    "script-src 'self' 'unsafe-inline' https://telegram.org",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self' data:",
    "media-src 'self' https:",
    "connect-src 'self' https://telegram.org https://*.telegram.org",
    "frame-src https://www.youtube.com https://www.youtube-nocookie.com",
    "worker-src 'self'",
    "manifest-src 'self'",
    "upgrade-insecure-requests"
  ].join("; "),
  "referrer-policy": "strict-origin-when-cross-origin",
  "permissions-policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=(), browsing-topics=()",
  "strict-transport-security": "max-age=31536000; includeSubDomains",
  "x-content-type-options": "nosniff",
  "x-dns-prefetch-control": "off",
  "x-permitted-cross-domain-policies": "none"
});
function headers(extra) {
  return Object.assign({}, SECURITY_HEADERS, extra || {});
}
function json(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, headers({
    "content-type": "application/json; charset=utf-8",
    "access-control-allow-origin": "*",
    "cache-control": "no-store",
    "content-length": Buffer.byteLength(body)
  }));
  res.end(body);
}
function readBody(req, limit) {
  return new Promise((resolve, reject) => {
    let size = 0; const chunks = [];
    req.on("data", (c) => { size += c.length; if (size > (limit || 1e6)) { reject(new Error("too large")); req.destroy(); } else chunks.push(c); });
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}
function sendFile(res, abs, code, req) {
  fs.readFile(abs, (err, buf) => {
    if (err) {
      const body = "not found";
      res.writeHead(404, headers({ "content-type": "text/plain; charset=utf-8", "cache-control": "no-store", "content-length": Buffer.byteLength(body) }));
      res.end(req && req.method === "HEAD" ? undefined : body);
      return;
    }
    const ext = path.extname(abs).toLowerCase();
    const mutable = ext === ".html" || ext === ".xml" || ext === ".txt" || ext === ".json" || ext === ".webmanifest" || path.basename(abs) === "sw.js";
    const cache = mutable ? "no-cache" : "public, max-age=86400, stale-while-revalidate=604800";
    res.writeHead(code || 200, headers({
      "content-type": MIME[ext] || "application/octet-stream",
      "cache-control": cache,
      "content-length": buf.length
    }));
    res.end(req && req.method === "HEAD" ? undefined : buf);
  });
}

function loadRedirects() {
  const rules = [];
  try {
    fs.readFileSync(path.join(ROOT, "_redirects"), "utf8").split("\n").forEach((line) => {
      const t = line.trim();
      if (!t || t.startsWith("#")) return;
      const parts = t.split(/\s+/);
      if (parts.length >= 2) {
        rules.push({ from: parts[0].replace(/\/+$/, "") || "/", to: parts[1], code: Number(parts[2]) || 301 });
      }
    });
  } catch (e) { /* none */ }
  return rules;
}
const REDIRECTS = loadRedirects();

/* Only deployable public artifacts are reachable. Repository source, reports,
 * workflows, tests, scripts and configuration are not web content. */
const PUBLIC_HTML_DIRS = new Set([
  "about", "anime", "article", "articles", "author", "channels", "contact",
  "copyright", "corrections", "disclaimer", "editorial-policy", "entertainment",
  "genre", "genres", "jobs", "make-money", "memes", "movie", "movies", "now",
  "privacy", "search", "series", "sports", "tech", "terms", "topic", "topics",
  "trending", "year", "years"
]);
const PUBLIC_ROOT_FILES = new Set([
  "index.html", "404.html", "robots.txt", "sitemap.xml", "news-sitemap.xml",
  "feed.xml", "manifest.webmanifest", "favicon.ico", "sw.js",
  "google2ec8f794263d784f.html", "yandex_78fdd841f95fa2e1.html",
  "1740cdb82c02b9af13911b38c853e85d2f708322fa0c2c55.txt"
]);
const PUBLIC_CONTENT_FILES = new Set([
  "competitions.json", "countries.json", "fpl.json", "money-coding.json",
  "money-remote.json", "money-writing.json", "sports-feed.json"
]);
const PUBLIC_DATA_FILES = new Set(["rec-data.json"]);
const PUBLIC_ASSET_EXT = new Set([".css", ".js", ".jpg", ".jpeg", ".png", ".svg", ".webp", ".gif", ".ico", ".mp3", ".mp4", ".webm", ".woff2"]);
const GONE_ROUTES = new Set([
  "/channels/trending", "/channels/latest", "/channels/netflix", "/channels/prime",
  "/channels/sony", "/channels/jio", "/channels/crunchyroll", "/channels/kids",
  "/channels/mx"
]);

function publicRelAllowed(rel) {
  const r = String(rel || "").replace(/^\/+/, "").replace(/\\/g, "/");
  if (!r || r.includes("\0")) return false;
  const parts = r.split("/").filter(Boolean);
  if (!parts.length || parts.some((part) => part.startsWith("."))) return false;
  if (parts.length === 1 && PUBLIC_ROOT_FILES.has(parts[0])) return true;
  const top = parts[0];
  if (top === "assets") return (parts.length === 1 || PUBLIC_ASSET_EXT.has(path.extname(parts[parts.length - 1]).toLowerCase()));
  if (PUBLIC_HTML_DIRS.has(top)) return parts.length === 1 || path.extname(parts[parts.length - 1]).toLowerCase() === ".html" || !path.extname(parts[parts.length - 1]);
  if (top === "content") return parts.length === 2 && PUBLIC_CONTENT_FILES.has(parts[1]);
  if (top === "data") return parts.length === 2 && PUBLIC_DATA_FILES.has(parts[1]);
  return false;
}

function safeAbs(reqPath) {
  let decoded;
  try { decoded = decodeURIComponent(String(reqPath || "/").split("?")[0]); }
  catch (e) { return null; }
  const rel = decoded.replace(/^\/+/, "");
  if (!publicRelAllowed(rel)) return null;
  const abs = path.normalize(path.join(ROOT, rel));
  if (abs !== ROOT && !abs.startsWith(ROOT + path.sep)) return null;
  return abs;
}

function safeExistingFile(abs) {
  try {
    if (!abs || !fs.statSync(abs).isFile()) return null;
    const real = fs.realpathSync(abs);
    return real.startsWith(ROOT + path.sep) ? real : null;
  } catch (e) { return null; }
}

function resolveWebsiteFile(pathname) {
  const p = pathname || "/";
  let abs = safeAbs(p);
  // Extensionless public paths are route directories, never arbitrary files.
  const direct = abs && path.extname(abs) ? safeExistingFile(abs) : null;
  if (direct) return direct;
  try {
    if (abs && fs.statSync(abs).isDirectory()) {
      const idx = safeExistingFile(path.join(abs, "index.html"));
      if (idx) return idx;
    }
  } catch (e) { /* missing */ }
  const asIndex = safeExistingFile(safeAbs((p.endsWith("/") ? p : p + "/") + "index.html"));
  return asIndex || null;
}

/* Article bodies may contain root-relative links (href="/..."). Inside the
 * Telegram webview those can resolve against the wrong base — absolutize. */
/* Telegram users stay IN the Mini App:
 *  - /article/<slug> links become in-app hash routes (the router handles them)
 *  - every other internal website link is unwrapped to plain text
 *  - images/assets stay absolute so they render; external citations stay live */
function absolutizeBody(html) {
  let h = String(html || "");
  h = h.replace(/ src="\/([a-z0-9_#-])/gi, ' src="https://bryme.onrender.com/$1');
  h = h.replace(/ href="(?:https:\/\/bryme\.onrender\.com)?\/article\/([a-z0-9-]+)\/?"/gi, ' href="#/article/$1"');
  h = h.replace(/<a\b[^>]*href="(?:https:\/\/bryme\.onrender\.com)?\/[^"]*"[^>]*>([\s\S]*?)<\/a>/gi, "$1");
  return h;
}

function publicPost(p, body) {
  return {
    title: p.title, slug: p.slug, category: p.category, categoryLabel: p.categoryLabel,
    excerpt: p.excerpt, image: p.image, publishedAt: p.publishedAt, author: p.author,
    readingTime: p.readingTime, url: p.url, miniAppRoute: "#/article/" + p.slug,
    status: "published", hasBody: Boolean(body)
  };
}

/* ---------- chats the bot has seen (group admin tooling) ---------- */
const chatsSeen = new Map();

/* ---------- request router ---------- */
const server = http.createServer(async (req, res) => {
  let url;
  try {
    const raw = String(req.url || "/");
    if (!raw.startsWith("/") || raw.startsWith("//")) throw new Error("invalid target");
    url = new URL(raw, "http://localhost");
  } catch (e) {
    return json(res, 400, { error: "bad_request" });
  }
  const rawPath = url.pathname;
  const p = rawPath.replace(/\/+$/, "") || "/";

  try {
    if (!new Set(["GET", "HEAD", "POST", "OPTIONS"]).has(req.method)) {
      res.writeHead(405, headers({ "allow": "GET, HEAD, POST, OPTIONS", "cache-control": "no-store" }));
      return res.end();
    }
    if (req.method === "OPTIONS" && p.startsWith("/api/")) {
      res.writeHead(204, headers({
        "access-control-allow-origin": "*",
        "access-control-allow-methods": "GET, HEAD, OPTIONS",
        "access-control-allow-headers": "content-type",
        "cache-control": "no-store"
      }));
      return res.end();
    }

    /* health */
    if (p === "/healthz") return json(res, 200, { ok: true, posts: loadContent().posts.length });

    /* ---- admin tooling (guarded by the webhook secret header) ---- */
    const authed = Boolean(SECRET) && req.headers["x-telegram-bot-api-secret-token"] === SECRET;
    if (p === "/admin/chats" && authed) {
      return json(res, 200, { chats: Array.from(chatsSeen.values()) });
    }
    if (p === "/admin/restrict" && authed && req.method === "POST") {
      const body = await readBody(req);
      const chatId = Number(JSON.parse(body || "{}").chat_id);
      if (!chatId) return json(res, 400, { ok: false, error: "chat_id required" });
      const r = await telegram("setChatPermissions", {
        chat_id: chatId,
        permissions: {
          can_send_messages: false, can_send_media_messages: false, can_send_polls: false,
          can_send_other_messages: false, can_add_web_page_previews: false,
          can_invite_users: true, can_pin_messages: false, can_change_info: false
        }
      });
      if (r && r.ok) await telegram("sendMessage", { chat_id: chatId, text: "🔒 This group is now announcement-only. Only admins can post — new members still get the full welcome. 🤖" });
      return json(res, 200, r);
    }

    /* ---- API ---- */
    if (p === "/api/sports/competitions") {
      const d = loadCompetitions();
      return json(res, 200, d || { builtAt: null, competitions: [] });
    }
    if (p === "/api/sports/leagues") {
      /* compat shape: tables only */
      const d = loadCompetitions();
      const leagues = d ? d.competitions.map((c) => ({ id: c.id, name: c.name, flag: c.flag, teams: c.teams })) : [];
      return json(res, 200, { builtAt: d ? d.builtAt : null, leagues });
    }
    if (p === "/api/money/opportunities") {
      const d = loadOpportunities();
      const list = ((d && d.opportunities) || [])
        .filter((o) => o.status === "published" && o.pay)
        .map((o) => ({
          slug: o.slug, publication: o.publication, title: o.title,
          excerpt: String(o.excerpt || "").slice(0, 180),
          pay: o.pay.display || "", usd: Math.round(usdEq(o.pay)),
          currency: o.pay.currency || "", types: o.writingTypeLabel || "",
          words: o.wordCount || "", lastVerified: o.lastVerified || (d ? d.updatedAt : ""),
          deadline: o.deadline || "",
          ng: o.pay.currency === "NGN" ||
              /nigeria|nigerian|africa|african|diaspora/i.test(
                String(o.eligibility && (o.eligibility.summary || "")) + " " + String(o.excerpt || "")),
          writingTypes: Array.isArray(o.writingTypes) ? o.writingTypes.slice(0, 6) : []
        }))
        .sort((a, b) => b.usd - a.usd);
      return json(res, 200, { updatedAt: (d && d.updatedAt) || null, count: list.length, opportunities: list });
    }
    if (p.startsWith("/api/money/opportunities/") && p.split("/").length === 5) {
      const d = loadOpportunities();
      const slug = decodeURIComponent(p.split("/")[4]);
      const o = ((d && d.opportunities) || []).find((x) => x.slug === slug);
      if (!o) return json(res, 404, { error: "not_found", message: "We couldn't find that market." });
      return json(res, 200, {
        slug: o.slug, publication: o.publication, title: o.title, excerpt: o.excerpt,
        pay: o.pay || null, deadline: o.deadline || "", wordCount: o.wordCount || "",
        writingTypeLabel: o.writingTypeLabel || "", experience: o.experience || "",
        eligibility: o.eligibility || "", whatTheyWant: o.whatTheyWant || "",
        whatTheyDontWant: o.whatTheyDontWant || "", howToSubmit: o.howToSubmit || "",
        response: o.response || "", rights: o.rights || "", requirements: o.requirements || "",
        applyUrl: o.applyUrl || "", applyEmail: o.applyEmail || "", officialUrl: o.officialUrl || "",
        lastVerified: o.lastVerified || "", updatedAt: (d && d.updatedAt) || "",
        disclaimer: (d && d.disclaimer) || ""
      });
    }
    if (p === "/api/money/remote-platforms") {
      let d = null;
      try { d = JSON.parse(fs.readFileSync(path.join(ROOT, "content", "remote-platforms.json"), "utf8")); }
      catch (e) { /* optional file */ }
      return json(res, 200, d || { count: 0, platforms: [] });
    }
    if (p === "/api/posts/latest") {
      const limit = Math.min(Number(url.searchParams.get("limit") || 8), 20);
      const { posts } = loadContent();
      return json(res, 200, { count: Math.min(limit, posts.length), posts: posts.slice(0, limit).map((x) => publicPost(x)) });
    }
    if (p.startsWith("/api/posts/category/")) {
      const cat = decodeURIComponent(p.split("/")[4] || "");
      const limit = Math.min(Number(url.searchParams.get("limit") || 12), 30);
      const { posts } = loadContent();
      const list = posts.filter((x) => x.category === cat).slice(0, limit);
      return json(res, 200, { category: cat, count: list.length, posts: list.map((x) => publicPost(x)) });
    }
    if (p.startsWith("/api/posts/") && p.split("/").length === 4) {
      /* retired-slug aliases: old bot buttons / shared links keep working */
      const SLUG_ALIASES = { "writing-opportunities": "writing" };
      let slug = decodeURIComponent(p.split("/")[3]);
      if (SLUG_ALIASES[slug]) slug = SLUG_ALIASES[slug];
      const { posts, bodies } = loadContent();
      const post = posts.find((x) => x.slug === slug);
      if (!post) return json(res, 404, { error: "not_found", message: "We couldn't find that article.", fallback: { miniAppRoute: "#/home", label: "Latest posts" } });
      return json(res, 200, Object.assign(publicPost(post, bodies[slug]), { body: absolutizeBody(bodies[slug] || "") }));
    }
    if (p === "/api/categories") {
      const { posts } = loadContent();
      const counts = {};
      posts.forEach((x) => (counts[x.category] = (counts[x.category] || 0) + 1));
      return json(res, 200, { categories: Object.entries(counts).map(([k, v]) => ({ key: k, count: v })) });
    }
    if (p === "/api/search") {
      const q = String(url.searchParams.get("q") || "").trim().toLowerCase();
      if (q.length < 2) return json(res, 200, { q, count: 0, results: [] });
      let cat = [];
      try { cat = JSON.parse(fs.readFileSync(path.join(ROOT, "content", "catalogue.json"), "utf8")); }
      catch (e) { cat = []; }
      const hits = (Array.isArray(cat) ? cat : [])
        .filter((x) => {
          const blob = ((x.title || "") + " " + (x.description || "") + " " + (x.genre || "") + " " + (x.slug || "")).toLowerCase();
          return blob.includes(q);
        })
        .slice(0, 20)
        .map((x) => ({
          title: x.title,
          slug: x.slug,
          year: x.year,
          genre: x.genre,
          url: "/movie/" + x.slug + "/"
        }));
      return json(res, 200, { q, count: hits.length, results: hits });
    }

    /* ---- Telegram webhook (off unless TELEGRAM_ENABLED=1) ---- */
    if (p === "/telegram/webhook") {
      if (!TELEGRAM_ON) return json(res, 404, { error: "telegram_disabled", message: "This service serves the website." });
      if (req.method !== "POST") return json(res, 405, { error: "method_not_allowed" });
      if (SECRET && req.headers["x-telegram-bot-api-secret-token"] !== SECRET) {
        return json(res, 401, { error: "unauthorized" });
      }
      let update;
      try { update = JSON.parse(await readBody(req)); } catch (e) { return json(res, 400, { error: "bad_json" }); }
      try {
        const c = update.message && update.message.chat;
        if (c && (c.type === "group" || c.type === "supergroup")) {
          chatsSeen.set(c.id, { id: c.id, title: c.title || "", type: c.type, ts: Date.now() });
        }
      } catch (e) {}
      json(res, 200, { ok: true }); // ack immediately; reply goes via Bot API
      try { await botFor(req).handleUpdate(update); } catch (e) { /* logged, never leaked */ }
      return;
    }

    /* Everything below is read-only public routing. */
    if (req.method !== "GET" && req.method !== "HEAD") {
      res.writeHead(405, headers({ "allow": "GET, HEAD", "cache-control": "no-store" }));
      return res.end();
    }

    /* ---- redirects from _redirects (duplicate movie/series URLs) ---- */
    const from = p.replace(/\/+$/, "") || "/";
    const rule = REDIRECTS.find((r) => r.from === from || r.from === p);
    if (rule) {
      res.writeHead(rule.code || 301, headers({
        "location": rule.to + (url.search || ""),
        "cache-control": "public, max-age=86400"
      }));
      return res.end();
    }

    /* Retired inferred-provider collections explain the removal while returning
     * a real 410, so crawlers do not treat them as active catalogue pages. */
    if (GONE_ROUTES.has(from)) {
      const gone = resolveWebsiteFile(from);
      if (gone) return sendFile(res, gone, 410, req);
      return json(res, 410, { error: "gone" });
    }

    /* ---- Mini App lives under /miniapp only — never at / ---- */
    if (p === "/miniapp" || p.startsWith("/miniapp/")) {
      const file = p === "/miniapp" || p === "/miniapp/" ? "index.html" : p.slice("/miniapp/".length);
      const abs = path.normalize(path.join(MINIAPP_DIR, file));
      const ext = path.extname(abs).toLowerCase();
      const real = safeExistingFile(abs);
      if (real && real.startsWith(MINIAPP_DIR + path.sep) && new Set([".html", ".css", ".js"]).has(ext)) {
        return sendFile(res, real, 200, req);
      }
    }

    /* ---- Public website (repo root) ---- */
    if (/\/index\.html$/i.test(rawPath)) {
      const target = rawPath.replace(/index\.html$/i, "") || "/";
      res.writeHead(308, headers({ "location": target + (url.search || ""), "cache-control": "public, max-age=86400" }));
      return res.end();
    }
    const page = resolveWebsiteFile(p === "/" ? "/index.html" : p);
    if (page && p !== "/" && !rawPath.endsWith("/") && path.basename(page) === "index.html") {
      res.writeHead(308, headers({ "location": rawPath + "/" + (url.search || ""), "cache-control": "public, max-age=86400" }));
      return res.end();
    }
    if (page) return sendFile(res, page, 200, req);

    const notFound = safeExistingFile(path.join(ROOT, "404.html"));
    if (notFound) return sendFile(res, notFound, 404, req);
    const body = "not found";
    res.writeHead(404, headers({ "content-type": "text/plain; charset=utf-8", "cache-control": "no-store", "content-length": Buffer.byteLength(body) }));
    res.end(req.method === "HEAD" ? undefined : body);
  } catch (e) {
    json(res, 500, { error: "internal", message: "Something went wrong. Try again." });
  }
});

if (!module.parent) {
  server.listen(PORT, "0.0.0.0", () => {
    console.log("BRYME website on :" + PORT + " | posts:", loadContent().posts.length,
      "| redirects:", REDIRECTS.length,
      "| telegram:", TELEGRAM_ON ? "on (/telegram/webhook only)" : "off");
  });
}
module.exports = { server, loadContent, telegram };
