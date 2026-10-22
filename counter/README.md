# Uptick visitor counter

A tiny service that counts how many different people visited the site in the past hour, so Uptick can show
"2,970 people visited Uptick in the past hour" and have it be true. It runs on Cloudflare Workers' free plan.

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/mortonezekiel/uptickauto/tree/main/counter)

## What it counts

- Every page view on the site sends one request to `POST /hit`.
- Each person counts once per rolling 60 minutes, however many pages they read, and drops out an hour after
  their last page view.
- People are told apart by a one-way hash of their IP address and browser, mixed with a secret key that only this
  service holds. IP addresses are never stored, hashes are deleted after about an hour, and no cookies are used.
- Bots, crawlers and headless browsers are skipped. Requests from other websites are refused. At most 4 people are
  counted per IP address, so nobody can pump up the number from one connection.
- People whose ad blocker blocks the request aren't counted, so if anything the number runs low.

## Set it up

1. Click the **Deploy to Cloudflare** button above. Sign in to Cloudflare (or make a free account), connect GitHub
   when asked, and press **Create and deploy**. Cloudflare copies this folder into a new repository in your
   GitHub account and deploys it.
2. When it finishes, copy the counter's address, which looks like
   `https://uptick-visitor-counter.YOUR-NAME.workers.dev`.
3. Put that address in `visitor_counter_url` in the site's `site.yaml`, rebuild and push.

## Endpoints

| Address | What it does |
|---|---|
| `GET /count` | The number of people in the past hour, as JSON. Open it in a browser anytime. |
| `POST /hit` | Records a page view and returns the new number. Only accepted from the site's own addresses. |

## Settings

- `ALLOWED_ORIGINS` in `wrangler.jsonc` lists the site addresses allowed to record visits.
- The free plan covers about 100,000 page views a day. Past that, the counter stops for the rest of the day
  (it resets at midnight UTC) and the site simply hides the notice. Cloudflare's $5-a-month plan removes the cap.

Changes made here don't reach a counter that's already deployed. Make them in the repository the Deploy button
created, and Cloudflare redeploys on every push.
