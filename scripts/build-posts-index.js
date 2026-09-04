#!/usr/bin/env node
/* Build content/posts-index.json + content/posts-bodies.json — the single
 * content source for the Telegram bot, the API and the Mini App.
 *
 * Everything is derived from the SAME files the website renders from:
 *   content/sports-articles.json, content/editorial.json,
 *   content/make-money-articles.json, content/opportunities.json,
 *   data/articles.json, content/matchweek-comics.json
 * plus (title/description parsed from the published HTML) the /tech/ and
 * /make-money/ section pages that exist only as static pages.
 *
 * Only published content is indexed. Re-run after publishing anything:
 *   node scripts/build-posts-index.js
 */
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const read = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), "utf8"));
const exists = (p) => fs.existsSync(path.join(ROOT, p));

const posts = [];
const bodies = {};

function add(p) {
  if (!p || !p.slug || !p.title) return;
  if (p.status && String(p.status).toLowerCase() !== "published") return;
  if (posts.some((x) => x.slug === p.slug)) return; // first source wins
  posts.push({
    slug: p.slug,
    title: p.title,
    excerpt: (p.excerpt || p.description || "").trim(),
    category: p.category,
    categoryLabel: p.categoryLabel,
    image: p.image || "",
    publishedAt: p.publishedAt || null,
    author: p.author || "BRYME",
    url: p.url,
    readingTime: p.readingTime || ""
  });
  if (p.body) bodies[p.slug] = p.body;
}

/* ---------- helpers for HTML-derived pages ---------- */
function bodyFromContent(content) {
  /* JSON article content: [{heading, body:[...paras] | "str"}] or [{text}] */
  if (!Array.isArray(content)) return "";
  const out = [];
  for (const block of content) {
    if (!block || typeof block !== "object") continue;
    if (block.heading) out.push("<h2>" + String(block.heading).replace(/<[^>]+>/g, "") + "</h2>");
    const b = block.body || block.text || block.paragraphs;
    if (typeof b === "string") out.push("<p>" + b.replace(/<[^>]+>/g, "") + "</p>");
    else if (Array.isArray(b)) b.forEach((t) => { if (t) out.push("<p>" + String(t).replace(/<[^>]+>/g, "") + "</p>"); });
    if (block.quote) out.push("<blockquote>" + String(block.quote).replace(/<[^>]+>/g, "") + "</blockquote>");
    if (Array.isArray(block.items)) out.push("<ul>" + block.items.map((i) => "<li>" + String(i).replace(/<[^>]+>/g, "") + "</li>").join("") + "</ul>");
  }
  return out.join("").slice(0, 24000);
}
function parseHtmlPage(relPath) {
  let rel = relPath.replace(/\/+$/, "");
  if (!rel.endsWith(".html")) rel += "/index.html";
  const abs = path.join(ROOT, rel);
  if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) return null;
  const html = fs.readFileSync(abs, "utf8");
  /* moved/removed stub pages are not content — keep them out of the index
   * (single source of truth: the real page at its canonical URL is the post) */
  const robots = (html.match(/name="robots" content="([^"]*)"/) || [])[1] || "";
  const stubDesc = (html.match(/name="description" content="([^"]*)"/) || [])[1] || "";
  if (/noindex/i.test(robots) || /catalogue has moved/i.test(stubDesc)) return null;
  const title = (html.match(/<title>([^<|]+)\|?\s*BRYME/i) || html.match(/<title>([^<]+)/) || [])[1];
  const desc = (html.match(/name="description" content="([^"]*)"/) || [])[1];
  const img = (html.match(/property="og:image" content="([^"]*)"/) || [])[1];
  const bodyMatch = html.match(/<article[^>]*>([\s\S]*?)<\/article>/i);
  const proseMatch = bodyMatch ? null : html.match(/class="prose[^"]*"[\s\S]*?>([\s\S]*?)<\/main>/i);
  const rawBody = bodyMatch ? bodyMatch[1] : proseMatch ? proseMatch[1] : "";
  return {
    title: title ? title.replace(/\s*BRYME\s*$/i, "").replace(/[|–-]\s*$/, "").trim() : null,
    desc: desc ? desc.trim() : "",
    img: img && !img.includes("bryme-card") ? "" : "", // hub cards only — no per-article art on these pages
    body: rawBody.replace(/<script[\s\S]*?<\/script>/gi, "").trim().slice(0, 24000)
  };
}

function addHtmlSection(dir, category, categoryLabel, urlBase, skip = []) {
  if (!exists(dir)) return;
  for (const name of fs.readdirSync(path.join(ROOT, dir)).sort()) {
    if (name === "index.html" || !name.endsWith(".html")) {
      // article pages live in slug/index.html dirs
    }
    const slugDir = path.join(ROOT, dir, name);
    if (!fs.statSync(slugDir).isDirectory()) continue;
    const page = parseHtmlPage(`${dir}/${name}/index.html`);
    if (!page || !page.title) continue;
    add({
      slug: name,
      title: page.title,
      excerpt: page.desc,
      category, categoryLabel,
      image: page.img,
      publishedAt: null,
      url: `/${dir}/${name}/`,
      body: page.body,
      status: "published"
    });
  }
  void skip;
}

/* ---------- 1. SPORTS ---------- */
(function () {
  const arts = read("content/sports-articles.json").articles || [];
  for (const a of arts) {
    const url = exists(`sports/articles/${a.slug}/index.html`)
      ? `/sports/articles/${a.slug}/`
      : exists(`sports/${a.slug}/index.html`) ? `/sports/${a.slug}/` : null;
    if (!url) continue; // not published on the site yet
    const page = parseHtmlPage(url.slice(1));
    const htmlBody = page ? page.body : "";
    const jsonBody = bodyFromContent(a.content);
    add({
      slug: a.slug, title: a.title, excerpt: a.excerpt || (page && page.desc) || "",
      category: "sports", categoryLabel: "⚽ Sports",
      image: "", publishedAt: a.publishedAt || null, author: a.author || "BRYME",
      url, readingTime: a.readingTime || "",
      body: htmlBody.length >= 1200 ? htmlBody : (jsonBody || htmlBody), status: a.status
    });
  }
})();

/* ---------- 2. COMICS ---------- */
(function () {
  const data = read("content/matchweek-comics.json");
  const stories = data.stories || [];
  stories.slice().reverse().forEach((s, i) => {
    if (s.status !== "complete") return;
    const slug = "comic-" + s.matchSlug;
    const art = data.art || {};
    const panels = (s.panels || []).map((p) => {
      /* panels are objects: { art, title, caption } — art keys map via data.art */
      const key = p && typeof p === "object" ? p.art : p;
      const src = (key && art[key]) || (typeof key === "string" && key.startsWith("/") ? key : "");
      if (!src) return "";
      const cap = p && p.title ? `<figcaption><b>${p.title}</b>${p.caption ? " — " + p.caption : ""}</figcaption>` : "";
      return `<figure class="comic-panel"><img src="${src}" alt="${s.headline || "BRYME comic panel"}" loading="lazy">${cap}</figure>`;
    }).join("");
    add({
      slug,
      title: s.headline,
      excerpt: s.resultLine + " — BRYME original football comic, Matchweek " + s.matchweek + ".",
      category: "comics", categoryLabel: "😂 Comics",
      image: "", publishedAt: null,
      url: "/sports/comics/",
      body: `<p><strong>${s.resultLine}</strong></p>${panels}`.slice(0, 24000),
      status: "published"
    });
    void i;
  });
})();

/* ---------- 3. MONEY ---------- */
(function () {
  for (const src of ["content/make-money-articles.json"]) {
    if (!exists(src)) continue;
    const arts = read(src);
    const list = Array.isArray(arts) ? arts : arts.articles || [];
    for (const a of list) {
      const slug = a.slug || a.id;
      const url = exists(`make-money/${slug}/index.html`) ? `/make-money/${slug}/` : null;
      if (!url) continue;
      const page = parseHtmlPage(url.slice(1));
      const htmlBody = page ? page.body : "";
      const jsonBody = bodyFromContent(a.content);
      add({
        slug, title: a.title, excerpt: a.excerpt || (page && page.desc) || "",
        category: "money", categoryLabel: "💰 Make Money",
        image: "", publishedAt: a.publishedAt || null, author: a.author || "BRYME",
        url, readingTime: a.readingTime || "",
        body: htmlBody.length >= 1200 ? htmlBody : (jsonBody || htmlBody), status: a.status
      });
    }
  }
  if (exists("content/opportunities.json")) {
    const ops = read("content/opportunities.json");
    const list = Array.isArray(ops) ? ops : ops.opportunities || [];
    for (const o of list) {
      const slug = o.slug || o.id;
      if (!slug) continue;
      const url = exists(`make-money/${slug}/index.html`) ? `/make-money/${slug}/` : null;
      if (!url) continue;
      const page = parseHtmlPage(url.slice(1));
      if (!page || !page.title) continue;
      add({
        slug, title: o.title || page.title, excerpt: o.excerpt || page.desc || "",
        category: "money", categoryLabel: "💰 Make Money",
        image: "", publishedAt: o.publishedAt || null, url, body: page.body, status: o.status || "published"
      });
    }
  }
  addHtmlSection("make-money", "money", "💰 Make Money", "/make-money/");
})();

/* ---------- 4. TECH & AI ---------- */
addHtmlSection("tech", "tech", "🤖 Tech & AI", "/tech/");

/* ---------- 5. ENTERTAINMENT (movies / series / anime) ---------- */
(function () {
  const map = [
    ["content/editorial.json", null],
    ["data/articles.json", null]
  ];
  for (const [src] of map) {
    if (!exists(src)) continue;
    const d = read(src);
    const list = Array.isArray(d) ? d : d.articles || [];
    for (const a of list) {
      const slug = a.slug || a.id;
      if (!slug) continue;
      const url = exists(`articles/${slug}/index.html`) ? `/articles/${slug}/`
        : exists(`article/${slug}/index.html`) ? `/article/${slug}/` : null;
      if (!url) continue;
      const page = parseHtmlPage(url.slice(1));
      const htmlBody = page ? page.body : "";
      const jsonBody = bodyFromContent(a.content || a.body || a.blocks);
      add({
        slug, title: a.title || page.title, excerpt: a.excerpt || a.description || page.desc || "",
        category: "entertainment", categoryLabel: "🎬 Movies & Anime",
        image: "", publishedAt: a.publishedAt || a.date || null,
        url, body: htmlBody.length >= 1200 ? htmlBody : (jsonBody || htmlBody), status: a.status || "published"
      });
    }
  }
})();

/* ---------- 6. INTERNET (digital discovery — subset of tech) ---------- */
(function () {
  const INTERNET = new Set(["useful-websites", "internet-tools", "best-streaming-apps-nigeria", "where-to-host-website-for-free", "signal-vs-whatsapp", "lyra-vs-spotify"]);
  for (const p of posts.slice()) {
    if (p.category === "tech" && INTERNET.has(p.slug)) {
      posts.push(Object.assign({}, p, {
        slug: "www-" + p.slug, category: "internet", categoryLabel: "🌐 Internet", url: p.url
      }));
    }
  }
})();

/* ---------- 6.5 BRYME DESK (editorial articles: entertainment + trading + sports) ---------- */
(function () {
  const d = read("content/desk-articles.json");
  for (const a of (d.articles || [])) {
    add({
      slug: a.slug, title: a.title, excerpt: a.excerpt,
      category: a.category, categoryLabel: a.categoryLabel,
      image: "", publishedAt: a.publishedAt, author: a.author,
      url: a.category === "sports" ? "/sports/" : a.category === "trading" ? "/sports/" : "/entertainment/",
      body: a.body, status: "published"
    });
  }
})();

/* ---------- 7. TRADING (tagged from any section) ---------- */
(function () {
  const RX = /trading|crypto|invest|forex|stock market/i;
  for (const p of posts.slice()) {
    if (p.category !== "trading" && (RX.test(p.title) || RX.test(p.excerpt))) {
      posts.push(Object.assign({}, p, { slug: "trd-" + p.slug, category: "trading", categoryLabel: "📈 Trading" }));
    }
  }
})();

/* ---------- write ---------- */
posts.sort((a, b) => (b.publishedAt || "") < (a.publishedAt || "") ? -1 : 1); // dated newest first
const out = { builtAt: new Date().toISOString(), categories: ["money", "tech", "sports", "entertainment", "trading", "internet", "comics"], posts };
fs.writeFileSync(path.join(ROOT, "content", "posts-index.json"), JSON.stringify(out));
fs.writeFileSync(path.join(ROOT, "content", "posts-bodies.json"), JSON.stringify(bodies));

const byCat = {};
posts.forEach((p) => (byCat[p.category] = (byCat[p.category] || 0) + 1));
console.log("posts-index.json:", posts.length, "posts");
console.log("  ", JSON.stringify(byCat));
console.log("  bodies:", Object.keys(bodies).length, "articles with extractable body");
