# Landing page and waitlist (draft)

Draft for workstream 2.1. It is **not deployed** and **not part of the library** (A5, D3). The
single file [`index.html`](index.html) is a self-contained static page (inline CSS and JS, no
build step, no external scripts, about 33 KB). Open it in a browser to preview it, or run
`python3 -m http.server -d roadmap/landing-page` and visit `http://localhost:8000/?utm_source=test`.

What the page does: says honestly that the product is not built yet, pitches technical debt
tracking (TODOs first) to engineering managers and tech leads, shows an illustrative mock
dashboard and a pricing sketch in INR, links to the open-source library as proof of credibility,
and collects waitlist answers. Nothing is stored in the browser (no cookies, no `localStorage`).

> Nothing has been signed up for, created or bought. Everything below is for you to do.

## 1. Brand swap (one place)

The provisional name is **Fragmo**, pending [`../decision-name.md`](../decision-name.md)
(2.0 found that Mendo is taken). Two ways to change it:

1. Edit `var BRAND = 'Fragmo';` at the top of the inline script. It fills every `[data-brand]`
   element, the `<title>` and the meta tags, and is sent with each signup in a hidden `brand` field.
2. Or replace every copy, including the no-JavaScript fallbacks, in one go:

   ```bash
   sed -i 's/Fragmo/NewName/g' roadmap/landing-page/index.html
   ```

   On macOS use `sed -i '' ...`. The page contains no lowercase `fragmo`. If you later add a
   domain (canonical or `og:url` tags), put it in by hand.

Also change the "Mendo" placeholders elsewhere in `roadmap/` once the name is final (see the
2.0 notes in `PROGRESS.md`).

## 2. Hosting: options compared

| | GitHub Pages (separate public repo) | Cloudflare Pages |
|---|---|---|
| Cost | Free for public repositories. ⚠️ Check the current plans and limits. | Free tier. ⚠️ Check current limits (builds per month, files, bandwidth). |
| New account | None, you already use GitHub | Yes, a Cloudflare account (free) |
| Deploy | Push `index.html` to `main`, enable Pages (Settings, Pages, deploy from branch) | Connect the repo, or "direct upload" of the folder, no build command |
| Custom domain and HTTPS | Yes. ⚠️ Check DNS steps in the GitHub docs. | Yes, easiest if the domain's DNS is also on Cloudflare |
| Private repo | Needs a paid plan, so use a public repo (the page is public anyway) | Works with private repos |
| Extras | None | Redirects and headers files, optional Web Analytics (⚠️ check) |

**Recommendation:** GitHub Pages from a **separate public repo** (not this one: this repo's
Pages site hosts the docs). It needs no new account, deploys on `git push`, and the page has no
secrets. Move to Cloudflare Pages only if you want a private repo, richer redirects or to keep the
domain's DNS there. Create the repo only after the name is decided (the repo name appears in the
default URL; with a custom domain it does not matter). Copy `index.html` as the repo's
`index.html`.

## 3. Wire the form so signups land in a Google Sheet

The page posts the form with `fetch` (`mode: 'no-cors'`) to the `FORM_ENDPOINT` constant near the
top of the script. While it is empty, the form validates and then shows "Not wired up yet".
Fields sent: `email`, `company_size`, `repos`, `current_tool`, `pay_intent` (yes, maybe, no),
`next_source` (repeated once per checkbox), `interview_ok` (`yes`, present only when the optional "OK to contact me for a 20-minute interview" box is ticked), plus hidden `utm_source`, `utm_medium`,
`utm_campaign`, `referrer` and `brand`.

Because the response is opaque with `no-cors`, the page shows "You're on the list" whenever the
request leaves the browser. Check the sheet yourself after the first test.

### Option A (recommended): Google Apps Script web app, ends in a Sheet you own

1. Create a Google Sheet with a header row:
   `timestamp, email, company_size, repos, current_tool, pay_intent, next_source, interview_ok, utm_source, utm_medium, utm_campaign, referrer, brand`.
2. Extensions, Apps Script, paste:

   ```javascript
   function doPost(e) {
     var p = e.parameter;
     var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
     sheet.appendRow([
       new Date(), p.email, p.company_size, p.repos, p.current_tool, p.pay_intent,
       (e.parameters.next_source || []).join('; '),
       p.interview_ok || 'no',
       p.utm_source, p.utm_medium, p.utm_campaign, p.referrer, p.brand
     ]);
     return ContentService.createTextOutput('ok');
   }
   ```

3. Deploy, New deployment, type "Web app", execute as **Me**, access **Anyone**. Copy the
   `/exec` URL into `FORM_ENDPOINT`. ⚠️ Google changes this UI and its quotas; check the current
   Apps Script docs. Anyone with the URL can post rows, so treat the sheet as untrusted input
   (spreadsheet formula injection: do not paste cells into other sheets without checking, or
   prefix risky values with an apostrophe in the script).
4. Submit a test from the page and confirm the row appears.

### Option B: Formspree

Create a form in Formspree, put its endpoint URL in `FORM_ENDPOINT`, and read signups in its
dashboard or export CSV. ⚠️ Check the current free-tier limit on submissions per month and
whether a Google Sheets integration is on the free plan. For a sheet you can see, use option A or
connect Formspree to Sheets only if the free plan allows it.

### Option C: Tally or Google Forms

Both are happier with their own form than with a custom HTML form. Tally has no plain "post here"
endpoint (⚠️ verify), and Google Forms' `formResponse` URL needs `entry.NNN` field names that
would replace the names used here. If you prefer one of them, build the form there (same six
questions plus the interview box), embed it or link to it in place of the `<form>`, and use their Google Sheets
integration (⚠️ check the free-tier limits, which have changed before). Tally supports hidden
fields filled from the URL (⚠️ verify), which would carry the UTM values. You then lose the
page's own hidden-field capture, so option A or B keeps attribution simplest.

## 4. Analytics: visits by source

There is a commented-out slot in `<head>` for **Plausible** or **Umami** (⚠️ check current
pricing: Plausible is paid after a trial, Umami Cloud has a free tier, and Umami can be
self-hosted for the cost of a small server). Pick one, copy the *current* snippet from its
dashboard (the one in the comment may be out of date), and uncomment it. Both are cookie-free
and record the referrer and `utm_*` values of each visit, which gives you "visits by source".

Signups by source come from the hidden form fields, so the sheet itself answers "which post
brought the signups". Use tagged links when you share the page, for example:

```text
https://YOUR-DOMAIN/?utm_source=hackernews&utm_medium=post&utm_campaign=launch-1-5
https://YOUR-DOMAIN/?utm_source=linkedin&utm_medium=social&utm_campaign=interviews
```

If you do not enable analytics, keep the privacy line accurate: it mentions only the referrer
and `utm_` tags that go into the form. If you add analytics, mention it there.

## 5. Things to finish before launch

- **USD note:** the pricing section has one visible line "USD equivalents: to be added by the
  maintainer" (`data-usd`). Add the numbers or delete the line.
- **Contact for removal:** the privacy line says "reply to any email we send". Make sure there
  is a real sender address when you first email the list.
- **Prices and tiers** are an illustrative test (spec 2.1). Do not turn them into an offer.
- Optional: add a canonical URL, `og:url` and an `og:image` once the domain exists.

## 6. Pre-launch checklist (acceptance criteria of 2.1)

- [ ] **Name decided** (`decision-name.md`), brand swapped (section 1), no "Mendo" on the page.
- [ ] **Live before 1.5 launches:** hosted (section 2), HTTPS works, the page opens at 360 px
      and in dark mode.
- [ ] **Signups arrive in a sheet you can see:** `FORM_ENDPOINT` set (section 3), a test
      submission created a row with all columns, including `pay_intent`, `next_source` and `interview_ok` (`yes` when the box was ticked, `no` otherwise).
- [ ] **Analytics record visits by source:** snippet enabled (section 4), a visit to
      `/?utm_source=test` shows up with that source, a test signup shows `utm_source=test`
      in the sheet.
- [ ] **Honesty:** the "not built yet" banner at the top and the note in the footer are still
      there, the mock dashboard still says "illustrative", no testimonials or counts were added.
- [ ] Privacy line matches what you really collect.
- [ ] Links to the GitHub repo and docs work (they point at the current URLs).

## 7. Where to link it from (follow-up, not done yet)

The library README was **not** changed, because there is no URL yet. After the page is live, add:

1. `README.md`: a line "Team dashboard coming soon: join the waitlist" with the page URL
   (near the top, below the badges or in the features list).
2. The docs (`site_src/`): the home page and, optionally, the CI page.
3. `integrations/github-action/README.md` (and the future `todonotifier-action` repo): one line
   at the end.

Keep the wording honest in each place (waitlist for early access, product not built yet), and
use UTM-tagged links per place (`utm_source=readme`, `utm_source=docs`, `utm_source=action`) to
see which one brings signups.
