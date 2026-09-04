/* BRYME Telegram bot logic — pure module.
 * server.js feeds it Telegram updates and a `send` function that performs
 * HTTP calls to the Telegram Bot API. All content comes from the shared
 * posts index (content/posts-index.json) — never hard-coded copies.
 *
 * Callback data vocabulary (stable, <=64 bytes):
 *   cat:<category>   open a category snippet
 *   latest           newest posts menu
 *   art:<slug>       one article snippet
 */
"use strict";

const CATEGORIES = [
  { key: "money",         label: "💰 Make Money",      emoji: "💰" },
  { key: "tech",          label: "🤖 Tech & AI",       emoji: "🤖" },
  { key: "sports",        label: "⚽ Sports",          emoji: "⚽" },
  { key: "entertainment", label: "🎬 Movies & Anime",  emoji: "🎬" },
  { key: "trading",       label: "📈 Trading",         emoji: "📈" },
  { key: "internet",      label: "🌐 Internet",        emoji: "🌐" },
  { key: "comics",        label: "😂 Comics",          emoji: "😂" }
];
const CAT_BY_KEY = {};
CATEGORIES.forEach((c) => (CAT_BY_KEY[c.key] = c));

/* Mini App route path per category */
function miniRoute(category) {
  return category === "entertainment" ? "movies" : category;
}

/* Destination-aware Mini App button URL.
 * The destination rides in TWO carriers so no Telegram client quirk
 * (fragment stripping / param injection / redirects) can drop it:
 *   1. query param  r=<route>   (e.g. miniapp?api=X&r=money)
 *   2. URL fragment  #/<route>  (e.g. miniapp?api=X&r=money#/money)
 * The app reads hash first, then r, then Telegram startapp params. */
function btnUrl(miniAppBase, route) {
  const sep = miniAppBase.indexOf("?") > -1 ? "&" : "?";
  return miniAppBase + sep + "r=" + encodeURIComponent(route) + "#/" + route;
}

function clip(text, n) {
  text = String(text || "").trim();
  return text.length > n ? text.slice(0, n - 1).replace(/\s+\S*$/, "") + "…" : text;
}

function homeKeyboard() {
  const rows = [];
  const row = [];
  CATEGORIES.forEach((c) => {
    row.push({ text: c.label, callback_data: "cat:" + c.key });
    if (row.length === 2) { rows.push(row.splice(0, 2)); }
  });
  if (row.length) rows.push(row.slice());
  rows.push([{ text: "🆕 Latest Posts", callback_data: "latest" }]);
  return { inline_keyboard: rows };
}

function homeText() {
  return "🔥 BRYME\n\n«What do you want to explore?»";
}

/* Daily rotating "opportunity teaser" — the Telegram money hook. */
function opportunityMessage(opps, miniAppBase) {
  if (!opps || !opps.length) return null;
  const pool = opps.slice(0, 10);
  const day = Math.floor(Date.now() / 864e5);
  const o = pool[day % pool.length];
  const amount = String((o.pay && o.pay.display) || "").replace(/\(.*?\)/g, "").trim().split(/\s+/).slice(0, 4).join(" ");
  return {
    o: o,
    text:
      "💰 MAKE " + amount.toUpperCase() + " WRITING?\n\n" +
      "What if you could spend 10 minutes preparing an article and submitting it — without paying anyone a dime?\n\n" +
      "One platform worth checking: " + o.publication + ".\n\n" +
      "✍️ What they accept\n💵 How payment works\n🇳🇬 What Nigerian writers need to know\n📝 A simple 3-step submission process\n\n" +
      "And no — you don't pay BRYME to access this opportunity.",
    keyboard: { inline_keyboard: [
      [{ text: "🚀 Open Make Money", web_app: { url: btnUrl(miniAppBase, "money") } }],
      [{ text: "💼 Browse the markets", web_app: { url: btnUrl(miniAppBase, "markets") } }],
      [{ text: "🔄 Another opportunity", callback_data: "cat:money" }, { text: "🆕 Latest", callback_data: "latest" }]
    ] }
  };
}

/* Markets message — its own single web_app button (one web_app per message). */
function marketsMessage(count, miniAppBase) {
  return {
    text: "💼 VERIFIED MARKETS\n\n" + count + " publications that pay for writing — real rates, verified by the BRYME desk. Sorted by what they pay.\n\nYou never pay to access these.",
    keyboard: { inline_keyboard: [
      [{ text: "💼 Open the markets list", web_app: { url: btnUrl(miniAppBase, "markets") } }],
      [{ text: "🏠 Menu", callback_data: "home" }]
    ] }
  };
}

/* Group greeting — fired when someone joins a chat the bot administers. */
function welcomeMessage(users, miniAppBase) {
  const names = users.filter((u) => u && !u.is_bot).map((u) => u.first_name || "friend");
  const who = names.length ? names.join(", ") : "friend";
  return {
    text:
      "👋 " + who + " — welcome to BRYME.\n\n" +
      "🛑 STOP SCROLLING. You just walked into the corner of Telegram that PAYS YOU.\n\n" +
      "💰 $75 per article — real publications, verified rates, and NIGERIA QUALIFIES ✅\n" +
      "💵 55 paid markets ($75–$580) + 20 remote platforms hiring for $15–100/hr\n" +
      "⚽ Live PL, La Liga & UCL tables, scores, scorers — updates itself every matchday\n" +
      "🤖 AI money tools · 🎬 what to watch next · 😂 matchweek comics\n\n" +
      "❌ No fees. ❌ No gurus. ❌ No \"pay first, earn later\" nonsense. Ever.\n\n" +
      "Your first $75 playbook is already open — one tap 👇",
    keyboard: { inline_keyboard: [
      [{ text: "🚀 CLAIM YOUR $75 PLAYBOOK — FREE", web_app: { url: btnUrl(miniAppBase, "market/afrolicious") } }],
      [{ text: "💼 All paid markets", web_app: { url: btnUrl(miniAppBase, "markets") } }],
      [{ text: "⚽ Sports", callback_data: "cat:sports" }, { text: "🆕 Latest", callback_data: "latest" }]
    ] }
  };
}

function categoryMessage(posts, category, miniAppBase, opps) {
  const cat = CAT_BY_KEY[category];
  if (!cat) return { text: "😕 Unknown section. Pick one below:", keyboard: homeKeyboard() };
  const list = posts.filter((p) => p.category === category);
  if (!list.length) {
    return {
      text: "«" + cat.label.toUpperCase() + "»\n\nNothing new here yet. Check back soon. 🌱",
      keyboard: { inline_keyboard: [[{ text: "🆕 Latest Posts", callback_data: "latest" }], [{ text: "🏠 Menu", callback_data: "home" }]] }
    };
  }
  const top = list[0];
  const more = list.length > 1 ? "\n\n +" + (list.length - 1) + " more in this section." : "";
  const rows = [
    [{ text: cat.emoji + " Open in BRYME", web_app: { url: btnUrl(miniAppBase, miniRoute(category)) } }]
  ];
  if (category === "money") {
    const tease = opportunityMessage(opps, miniAppBase);
    if (tease) {
      return {
        text: tease.text,
        keyboard: tease.keyboard
      };
    }
    rows.push([{ text: "💼 Verified paid markets", web_app: { url: btnUrl(miniAppBase, "markets") } }]);
  }
  rows.push([{ text: "🔄 Another one", callback_data: "cat:" + category }, { text: "🆕 Latest", callback_data: "latest" }]);
  return {
    text: "«" + cat.label.toUpperCase() + "»\n\n" + clip(top.title, 90) + "\n\n" + clip(top.excerpt, 220) + more,
    keyboard: { inline_keyboard: rows }
  };
}

function latestMessage(posts, miniAppBase) {
  const list = posts.slice(0, 8);
  if (!list.length) {
    return { text: "Nothing published yet. Check back soon. 🌱", keyboard: homeKeyboard() };
  }
  const rows = list.map((p) => [{
    text: p.categoryLabel.split(" ").slice(1).join(" ") + ": " + clip(p.title, 32),
    web_app: { url: btnUrl(miniAppBase, "article/" + p.slug) }
  }]);
  rows.push([{ text: "🏠 Menu", callback_data: "home" }]);
  return { text: "🆕 LATEST ON BRYME\n\nTap to read inside BRYME:", keyboard: { inline_keyboard: rows } };
}

function articleMessage(posts, slug, miniAppBase) {
  const p = posts.find((x) => x.slug === slug);
  if (!p) {
    return {
      text: "😕 We couldn't find that article.\n\nCheck the latest BRYME posts instead.",
      keyboard: { inline_keyboard: [[{ text: "🆕 Latest Posts", callback_data: "latest" }], [{ text: "🏠 Menu", callback_data: "home" }]] }
    };
  }
  return {
    text: "«" + clip(p.title, 90).toUpperCase() + "»\n\n" + clip(p.excerpt, 240) + "\n\n🚀 Continue reading in BRYME",
    keyboard: {
      inline_keyboard: [
        [{ text: "🚀 Open in BRYME", web_app: { url: btnUrl(miniAppBase, "article/" + p.slug) } }],
        [{ text: "🏠 Menu", callback_data: "home" }]
      ]
    }
  };
}

/* Create the bot. deps: { getPosts(), miniAppBase, apiBaseUrl, send(method, payload), answerCallback(id, text) } */
function createBot(deps) {
  const { getPosts, miniAppBase, send, answerCallback } = deps;
  /* When the Mini App is hosted on the FRONTEND domain (recommended:
   * https://bryme.onrender.com/miniapp/) it needs to be told where the
   * backend API lives — the app reads ?api= from its URL. When the Mini App
   * is hosted by the backend itself, no parameter is needed. */
  const apiParam = deps.apiBaseUrl
    ? (deps.apiBaseUrl.indexOf("?") > -1 ? "&" : "?") + "api=" + encodeURIComponent(deps.apiBaseUrl.replace(/\/+$/, ""))
    : "";
  const base = miniAppBase + apiParam + (apiParam ? "&" : "?") + "v=20260827-12";
  const opps = deps.getOpportunities ? deps.getOpportunities() : [];

  /* some chats (channels / broadcast-style supergroups) reject web_app buttons —
   * transparently retry with plain URL buttons so the message always lands */
  function urlFallbackKeyboard(kb) {
    if (!kb || !kb.inline_keyboard) return kb;
    const bot = (deps.botUsername || "").replace(/^@/, "");
    return {
      inline_keyboard: kb.inline_keyboard.map((row) =>
        row.map((b) => {
          if (!b.web_app) return b;
          /* prefer the bot funnel (opens native Mini App after one tap);
           * fall back to the raw URL if the username is unknown */
          if (!bot) return { text: b.text, url: b.web_app.url };
          const r = new URL(b.web_app.url, "https://x.example").searchParams.get("r") || "home";
          const start = r.startsWith("market/") ? r.slice(7) : r;
          return { text: b.text, url: "https://t.me/" + bot + "?start=" + encodeURIComponent(start) };
        })
      )
    };
  }
  function deliver(chatId, msg) {
    const payload = {
      chat_id: chatId,
      text: msg.text,
      parse_mode: "",
      disable_web_page_preview: true,
      reply_markup: msg.keyboard
    };
    return send("sendMessage", payload).then((r) => {
      if (r && r.ok === false && /BUTTON_TYPE_INVALID/i.test(String(r.description || ""))) {
        return send("sendMessage", Object.assign({}, payload, { reply_markup: urlFallbackKeyboard(msg.keyboard) }));
      }
      return r;
    }).catch(() => {});
  }

  function handleStart(chatId, arg) {
    const cat = (arg || "").trim().toLowerCase();
    if (cat && CAT_BY_KEY[cat]) {
      return deliver(chatId, categoryMessage(getPosts(), cat, base, opps));
    }
    if (cat === "latest") return deliver(chatId, latestMessage(getPosts(), base));
    if (cat === "markets") return deliver(chatId, marketsMessage(opps.length, base));
    const slug = cat;
    if (slug) {
      const opp = opps.find((x) => x.slug === slug);
      if (opp) return deliver(chatId, opportunityMessage([opp], base));
      const p = getPosts().find((x) => x.slug === slug);
      if (p) return deliver(chatId, articleMessage(getPosts(), slug, base));
    }
    return deliver(chatId, { text: homeText(), keyboard: homeKeyboard() });
  }

  /* batched greetings — collect joiners per chat for 90s, greet once */
  const joinWindow = new Map();
  function greetBatched(chatId, users) {
    const cur = joinWindow.get(chatId) || { users: [], timer: null };
    users.forEach((u) => { if (!cur.users.some((x) => x.id === u.id)) cur.users.push(u); });
    clearTimeout(cur.timer);
    cur.timer = setTimeout(() => {
      joinWindow.delete(chatId);
      deliver(chatId, welcomeMessage(cur.users, base));
    }, 90000);
    joinWindow.set(chatId, cur);
    return Promise.resolve();
  }

  /* Free-text intent -> section. First match wins. */
  const TEXT_MAP = [
    [/\b(money|make money|earn|earning|income|hustle)\b/i, "money"],
    [/\b(sport|sports|football|soccer|score|scores|fixture|fixtures|table|league|la liga)\b/i, "sports"],
    [/\b(tech|ai|a\.i|artificial|robot|gpt)\b/i, "tech"],
    [/\b(movie|movies|film|films|series|serie|anime|cinema|entertainment|watch|trailer)\b/i, "entertainment"],
    [/\b(trading|trade|trader|crypto|forex|stock|stocks|market)\b/i, "trading"],
    [/\b(internet|website|websites|tool|tools|online)\b/i, "internet"],
    [/\b(comic|comics|banter|funny|meme)\b/i, "comics"],
    [/\b(latest|new|news|fresh|update|updates)\b/i, "latest"]
  ];
  function textIntent(t) {
    const s = String(t || "").toLowerCase();
    for (let i = 0; i < TEXT_MAP.length; i++) if (TEXT_MAP[i][0].test(s)) return TEXT_MAP[i][1];
    return null;
  }

  return {
    handleUpdate(update) {
      try {
        const msg = update.message;
        const cb = update.callback_query;
        if (msg && Array.isArray(msg.new_chat_members) && msg.new_chat_members.length && !msg.text) {
          /* batch greetings: many joins in a short window = ONE welcome */
          const humans = msg.new_chat_members.filter((u) => u && !u.is_bot);
          if (humans.length) return greetBatched(msg.chat.id, humans);
        }
        if (msg && msg.text) {
          const parts = msg.text.split(/\s+/);
          const cmd = (parts[0] || "").replace(/@.*$/, "").toLowerCase();
          if (cmd === "/start") return handleStart(msg.chat.id, parts.slice(1).join(" "));
          if (cmd === "/menu" || cmd === "/help" || cmd === "/home") return handleStart(msg.chat.id);
          if (cmd === "/latest") return handleStart(msg.chat.id, "latest");
          const intent = textIntent(msg.text);
          if (intent === "latest") return deliver(msg.chat.id, latestMessage(getPosts(), base));
          if (intent) return deliver(msg.chat.id, categoryMessage(getPosts(), intent, base, opps));
          return deliver(msg.chat.id, {
            text: "🔥 BRYME\n\n«What do you want to explore?»\n(Tip: you can also type — try “make money”, “sports” or “comics”.)",
            keyboard: homeKeyboard()
          });
        }
        if (cb && cb.data) {
          const chatId = cb.message && cb.message.chat ? cb.message.chat.id : cb.from && cb.from.id;
          const done = answerCallback(cb.id).catch(() => {});
          if (cb.data === "home") return done.then(() => deliver(chatId, { text: homeText(), keyboard: homeKeyboard() }));
          if (cb.data === "latest") return done.then(() => deliver(chatId, latestMessage(getPosts(), base)));
          if (cb.data === "markets") return done.then(() => deliver(chatId, marketsMessage(opps.length, base)));
          if (cb.data.startsWith("cat:")) return done.then(() => deliver(chatId, categoryMessage(getPosts(), cb.data.slice(4), base, opps)));
          if (cb.data.startsWith("art:")) return done.then(() => deliver(chatId, articleMessage(getPosts(), cb.data.slice(4), base)));
          return done;
        }
      } catch (e) {
        /* never expose internals to users */
        const chatId = (update.message && update.message.chat && update.message.chat.id) ||
                       (update.callback_query && update.callback_query.from && update.callback_query.from.id);
        if (chatId) deliver(chatId, { text: "😕 Something went wrong on our side. Try again from the menu.", keyboard: homeKeyboard() });
      }
      return Promise.resolve();
    }
  };
}

module.exports = { createBot, CATEGORIES, homeText, homeKeyboard, categoryMessage, latestMessage, articleMessage, miniRoute };
