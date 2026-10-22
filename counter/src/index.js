// Uptick visitor counter
//
// Counts how many different people loaded a page on the site in the past 60 minutes, so the site can say
// "2,970 people visited Uptick in the past hour" and have it be true.
//
// How a visit is counted
// - Each page view on the site sends POST /hit. Requests from other websites are refused, and bots, crawlers
//   and headless browsers are skipped by their user agent.
// - A person is recognized by a one-way hash of their IP address and browser string, mixed with a random secret
//   that never leaves this service. The IP address itself is never stored.
// - Each person counts once however many pages they view, and drops out 60 minutes after their last page view.
//   At most MAX_PER_IP people are counted per IP address, so one connection can't pump up the number.
// - Hashes are deleted once they're more than about an hour old. No cookies, nothing saved in the browser.
// - If the service restarts, it reloads the last hour from storage. Anything it can't be sure of is left out,
//   so the number can run slightly low but never high.

import { DurableObject } from "cloudflare:workers";

const WINDOW_MS = 60 * 60 * 1000;
const REFRESH_MS = 30 * 60 * 1000; // save a returning visitor again at most this often
const MAX_PER_IP = 4;
const BOT_UA =
  /bot\b|bot\/|crawl|spider|slurp|mediapartners|adsbot|headless|lighthouse|pagespeed|prerender|phantom|selenium|puppeteer|playwright|curl|wget|python|okhttp|go-http|java\/|axios|node-fetch|libwww|httpclient/i;

const minuteOf = (ms) => Math.floor(ms / 60000);

function toHex(bytes) {
  let out = "";
  for (const b of bytes) out += b.toString(16).padStart(2, "0");
  return out;
}

export class VisitorWindow extends DurableObject {
  constructor(ctx, env) {
    super(ctx, env);
    this.sql = ctx.storage.sql;
    this.seen = new Map(); // visitor hash -> { last, saved, ip }
    this.perIp = new Map(); // IP hash -> Set of visitor hashes
    this.lastPrune = 0;
    ctx.blockConcurrencyWhile(async () => this.load());
  }

  load() {
    this.sql.exec("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)");
    this.sql.exec("CREATE TABLE IF NOT EXISTS buckets (minute INTEGER PRIMARY KEY, entries TEXT NOT NULL)");
    const row = this.sql.exec("SELECT value FROM meta WHERE key = 'salt'").toArray()[0];
    if (row) {
      this.salt = row.value;
    } else {
      this.salt = toHex(crypto.getRandomValues(new Uint8Array(32)));
      this.sql.exec("INSERT INTO meta (key, value) VALUES ('salt', ?)", this.salt);
    }
    // A reloaded visitor's last visit is taken as the start of the minute they were saved in, which is never
    // later than the truth.
    const from = minuteOf(Date.now() - WINDOW_MS);
    const rows = this.sql.exec("SELECT minute, entries FROM buckets WHERE minute >= ? ORDER BY minute", from).toArray();
    for (const { minute, entries } of rows) {
      const at = minute * 60000;
      for (const item of String(entries).split(" ")) {
        const [vid, ip] = item.split(".");
        if (vid && ip) this.remember(vid, ip, at, at);
      }
    }
  }

  remember(vid, ip, last, saved) {
    const current = this.seen.get(vid);
    if (current) {
      current.last = Math.max(current.last, last);
      current.saved = Math.max(current.saved, saved);
      return;
    }
    this.seen.set(vid, { last, saved, ip });
    let group = this.perIp.get(ip);
    if (!group) this.perIp.set(ip, (group = new Set()));
    group.add(vid);
  }

  forget(vid, entry) {
    this.seen.delete(vid);
    const group = this.perIp.get(entry.ip);
    if (group) {
      group.delete(vid);
      if (!group.size) this.perIp.delete(entry.ip);
    }
  }

  prune(now) {
    const cutoff = now - WINDOW_MS;
    for (const [vid, entry] of this.seen) {
      if (entry.last <= cutoff) this.forget(vid, entry);
    }
    if (now - this.lastPrune >= 60000) {
      this.lastPrune = now;
      this.sql.exec("DELETE FROM buckets WHERE minute < ?", minuteOf(cutoff) - 1);
    }
  }

  save(now, vid, ip) {
    this.sql.exec(
      "INSERT INTO buckets (minute, entries) VALUES (?, ?) " +
        "ON CONFLICT(minute) DO UPDATE SET entries = entries || ' ' || excluded.entries",
      minuteOf(now),
      `${vid}.${ip}`,
    );
  }

  async hash(text) {
    const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${this.salt}|${text}`));
    return toHex(new Uint8Array(digest).slice(0, 12));
  }

  // Records one page view and returns how many different people visited in the past 60 minutes.
  async hit(ipAddress, userAgent) {
    const [vid, ip] = await Promise.all([this.hash(`v|${ipAddress}|${userAgent}`), this.hash(`i|${ipAddress}`)]);
    const now = Date.now();
    this.prune(now);
    const entry = this.seen.get(vid);
    if (entry) {
      entry.last = now;
      if (now - entry.saved >= REFRESH_MS) {
        this.save(now, vid, entry.ip);
        entry.saved = now;
      }
      return this.seen.size;
    }
    const group = this.perIp.get(ip);
    if (group && group.size >= MAX_PER_IP) return this.seen.size;
    this.remember(vid, ip, now, now);
    this.save(now, vid, ip);
    return this.seen.size;
  }

  // Returns the current count without recording anything.
  visitors() {
    this.prune(Date.now());
    return this.seen.size;
  }
}

function reply(body, status, headers) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...headers },
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin");
    const allowed = String(env.ALLOWED_ORIGINS || "")
      .split(",")
      .map((s) => s.trim().replace(/\/+$/, ""))
      .filter(Boolean);
    const fromSite = origin !== null && allowed.includes(origin);
    const cors = fromSite ? { "Access-Control-Allow-Origin": origin, Vary: "Origin" } : { Vary: "Origin" };

    if (request.method === "OPTIONS") {
      return new Response(null, {
        status: 204,
        headers: { ...cors, "Access-Control-Allow-Methods": "GET, POST, OPTIONS", "Access-Control-Max-Age": "86400" },
      });
    }

    const counter = env.VISITORS.get(env.VISITORS.idFromName("visitors"));

    if (url.pathname === "/hit") {
      if (request.method !== "POST") return reply({ error: "Use POST." }, 405, { ...cors, Allow: "POST" });
      if (!fromSite) return reply({ error: "This counter only accepts visits from the site itself." }, 403, cors);
      const ip = request.headers.get("CF-Connecting-IP");
      const ua = request.headers.get("User-Agent") || "";
      const counted = Boolean(ip) && ua.length > 0 && !BOT_UA.test(ua);
      const visitors = counted ? await counter.hit(ip, ua) : await counter.visitors();
      return reply({ visitors, window_minutes: 60, counted }, 200, cors);
    }

    if (url.pathname === "/count" && (request.method === "GET" || request.method === "HEAD")) {
      const visitors = await counter.visitors();
      return reply({ visitors, window_minutes: 60 }, 200, { "Access-Control-Allow-Origin": "*" });
    }

    if (url.pathname === "/") {
      return reply(
        { service: "Uptick visitor counter", live_count: `${url.origin}/count`, window_minutes: 60 },
        200,
        { "Access-Control-Allow-Origin": "*" },
      );
    }

    return reply({ error: "Not found." }, 404, cors);
  },
};
