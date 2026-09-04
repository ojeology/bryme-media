#!/usr/bin/env node
/* Telegram bot setup helper.
 *
 *   node scripts/setup-telegram.js --set-webhook https://YOUR-SERVICE.onrender.com
 *   node scripts/setup-telegram.js --info
 *   node scripts/setup-telegram.js --send-start 123456789   (test a chat id)
 *   node scripts/setup-telegram.js --set-menu-button https://YOUR-SERVICE.onrender.com
 *
 * Requires TELEGRAM_BOT_TOKEN in the environment (never hard-coded).
 * The webhook secret is generated and printed if TELEGRAM_WEBHOOK_SECRET is unset.
 */
"use strict";
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..");
const args = process.argv.slice(2);
const get = (f) => { const i = args.indexOf(f); return i > -1 ? args[i + 1] : undefined; };

const TOKEN = process.env.TELEGRAM_BOT_TOKEN;
if (!TOKEN) { console.error("Set TELEGRAM_BOT_TOKEN first (env var)."); process.exit(1); }
const API = (process.env.TELEGRAM_API_BASE || "https://api.telegram.org") + "/bot" + TOKEN + "/";

function tg(method, payload) {
  return fetch(API + method, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload || {}) })
    .then((r) => r.json());
}

(async () => {
  const cmd = args[0] || "--info";
  if (cmd === "--info") {
    const me = await tg("getMe");
    console.log(JSON.stringify(me.result, null, 2));
  } else if (cmd === "--set-webhook") {
    const base = get("--set-webhook");
    if (!base) { console.error("usage: --set-webhook https://host"); process.exit(1); }
    let secret = process.env.TELEGRAM_WEBHOOK_SECRET;
    let generated = false;
    if (!secret) {
      secret = require("crypto").randomBytes(24).toString("hex");
      generated = true;
    }
    const res = await tg("setWebhook", {
      url: base.replace(/\/+$/, "") + "/telegram/webhook",
      secret_token: secret,
      allowed_updates: ["message", "callback_query"],
      drop_pending_updates: false
    });
    console.log("setWebhook:", JSON.stringify(res));
    if (generated) {
      console.log("\nTELEGRAM_WEBHOOK_SECRET=" + secret);
      console.log("^ save this as an env var on the service, or the webhook will reject updates.");
    }
  } else if (cmd === "--set-menu-button") {
    const base = get("--set-menu-button");
    const res = await tg("setChatMenuButton", { menu_button: { type: "web_app", text: "BRYME", web_app: { url: base.replace(/\/+$/, "") + "/#/home" } } });
    console.log("setChatMenuButton:", JSON.stringify(res));
  } else if (cmd === "--delete-webhook") {
    console.log(JSON.stringify(await tg("deleteWebhook")));
  } else if (cmd === "--send-start") {
    const chatId = get("--send-start");
    const posts = JSON.parse(fs.readFileSync(path.join(ROOT, "content", "posts-index.json"), "utf8")).posts;
    const { createBot } = require(path.join(ROOT, "server", "bot.js"));
    const bot = createBot({
      getPosts: () => posts,
      miniAppBase: (get("--mini") || "https://example.com").replace(/\/+$/, ""),
      send: (m, p) => tg(m, p),
      answerCallback: (id) => tg("answerCallbackQuery", { callback_query_id: id })
    });
    await bot.handleUpdate({ message: { chat: { id: Number(chatId) }, text: "/start " + (args.slice(args.indexOf("--send-start") + 2).join(" ") || "") } });
    console.log("sent /start to", chatId);
  } else {
    console.error("unknown command");
  }
})().catch((e) => { console.error(e.message); process.exit(1); });
