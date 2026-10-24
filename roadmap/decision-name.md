# Decision: SaaS name and brand (workstream 2.0)

**Status: Recommendation pending maintainer checks.** The maintainer decides (D6). Nothing here
is bought, registered or reserved, and the "Mendo" placeholder across `roadmap/` is **not**
replaced yet. Replace it only after the "Final decision" section below is filled in.

Research date: 2026-10-24 (the shortlist's own quick checks were done on 2026-10-23).

> ⚠️ **This is not legal clearance and not a domain purchase check.** Everything marked ⚠️ could
> not be verified from this sandbox, or is an inference. The trademark attorney check, the
> language check with real people and the recall test are human steps. Kits for them are below.

## 1. Summary

| | |
|---|---|
| **Recommendation** | Do **not** go ahead with **Mendo**. Take **Fragmo** forward as the provisional choice, and run the human checks (section 8) on it first. Keep **Paydown** as the fallback. Drop **Mora**. |
| **Why, in one line** | Mendo is already a funded B2B SaaS company in the same software classes, and its domains are gone. Fragmo has no product found and most of its domains and handles are free, but it has a real "frag" problem that only the human tests can clear. |
| **Biggest single finding** | A Paris company called **Mendo** (website `mendo.cloud`) raised a EUR 12 million Series A in June 2026 for an enterprise GenAI adoption and analytics SaaS used by 100+ large organisations. The roadmap's Phase 3 working repo name is `mendo-cloud`, which is literally their domain. |
| **Confidence** | Medium. The Mendo conflict is well sourced (several news and funding sites agree). The Fragmo "clear" result rests on one web search, an RDAP lookup and registry lookups, so it can be wrong. |

## 2. Evidence: side by side

How the checks were run: RDAP through `https://rdap.org/domain/<domain>` (HTTP 200 = registered,
404 = probably unregistered); PyPI JSON API; npm registry; 5 web searches or fetches. About 31
`curl` calls in total. Registration and expiry dates come from the RDAP `events`.

### 2.1 Domains

"Parked?" is only a guess from the nameservers, because no page was fetched. The "Check at
registrar" column is left blank on purpose: no price source was found and prices must not be
invented. Fill it in (INR, including GST and renewal price) when you look at a registrar.

| Domain | Mendo | Check at registrar | Fragmo | Check at registrar |
|---|---|---|---|---|
| `.com` | **Registered** since 1998-07-09, expires 2027-07-08. Nameservers `DNS1.MCN.ORG`. ⚠️ Unknown owner, long-held. | | **Registered** since 2019-05-13, expires 2027-05-13. Nameservers `NS1.SQUADHELP.COM`, so ⚠️ it is probably listed for sale on the Squadhelp naming marketplace. Price unknown. | |
| `.dev` | **Registered** since 2023-01-25, expires 2027-01-25. Nameservers DigitalOcean (in use or parked, ⚠️ unknown). | | **Looks free** (RDAP 404 from the registry). | |
| `.io` | ⚠️ **Manual.** RDAP has no service for `.io` (rdap.org: "No RDAP service is available"); its 404 does not mean free. | | ⚠️ **Manual**, same reason. | |
| `.app` | **Registered** since 2024-04-18, expires 2027-04-18. Nameservers Namecheap (`registrar-servers.com`), ⚠️ probably parked or reselling. | | **Registered** since 2026-08-25 (two months ago), expires 2027-08-25. Nameservers Cloudflare. ⚠️ Could be a new project or an investor. Unknown. | |
| `get<name>.com` | **Registered** since 2026-06-10 (just before the Series A news), GoDaddy nameservers, locked. ⚠️ Likely the Paris company, an inference. | | **Looks free** (RDAP 404). | |
| `<name>hq.com` | **Registered** since 2025-10-31, expires **2026-10-31**, Cloudflare. ⚠️ Expires in a week; it will most likely renew or go into a grace period, so do not count on it. | | **Looks free** (RDAP 404). | |

Fallback names (domains and package names only):

| Domain | Paydown | Mora |
|---|---|---|
| `.com` | **Registered** since 2001-02-05, expires 2034-02-05, fully locked. Long-term holder. | **Registered** since 1994-04-18, expires 2032-04-19. |
| `.dev` | **Looks free** (RDAP 404). | **Registered** since 2019-02-28. |
| `.app` | **Registered** since 2025-03-28 (Namecheap). | **Registered** since 2018-05-11, expires 2029. |
| `.io` | ⚠️ Manual (no RDAP). | ⚠️ Manual (no RDAP). |

The `get<name>.com` and `<name>hq.com` forms were not checked for the fallbacks, to save budget.

### 2.2 Handles

The sandbox blocks `api.github.com` ("sessions are bound to their configured repositories"),
so GitHub was **not** checked with `curl` (HTTP 403 from the proxy, not from GitHub).
A GitHub user search through the GitHub tool did not list an exact `mendo` login in its first
five hits, but a search is not an availability check. Treat GitHub as ⚠️ **manual** for all four names.

| Handle | Mendo | Fragmo | Paydown | Mora |
|---|---|---|---|---|
| GitHub user or org | ⚠️ Manual: https://github.com/mendo | ⚠️ Manual: https://github.com/fragmo | ⚠️ Manual: https://github.com/paydown | ⚠️ Manual: https://github.com/mora |
| PyPI | **Free** (404) | **Free** (404) | **Free** (404) | **Taken** (200) |
| npm | **Free** (404) | **Free** (404) | **Taken** (200) | **Taken** (200) |
| X | ⚠️ Manual: https://x.com/mendo | ⚠️ Manual: https://x.com/fragmo | not checked | not checked |
| LinkedIn page | ⚠️ Manual: https://www.linkedin.com/company/mendo (⚠️ very likely the Paris company) | ⚠️ Manual: https://www.linkedin.com/company/fragmo | not checked | not checked |
| GitHub Marketplace listing name | ⚠️ Manual: https://github.com/marketplace?query=mendo | ⚠️ Manual: https://github.com/marketplace?query=fragmo | not checked | not checked |

PyPI and npm "free" only means nobody has published under the exact name today. Squatting and
similar-name rules are not checked. Nothing was reserved.

### 2.3 Trademarks and existing products (web search, not a register search)

| | Mendo | Fragmo |
|---|---|---|
| Existing software or SaaS with the name | **Yes, a direct conflict.** Mendo, Paris: enterprise GenAI adoption and analytics platform (MendoGPT, integrates with Microsoft 365 Copilot, ChatGPT, Gemini, Claude). Website `mendo.cloud` (⚠️ from one aggregator, not confirmed on the company site). Raised EUR 3.5 million in late 2024 and a EUR 12 million Series A in June 2026 (Ventech, Educapital). Customers reported: 100+ large organisations. About 50 staff, planning 100. | **None found** in one search. The nearest hits are different names: FragMob, Fragmemo (iOS memo app), FragR (rock-fragmentation app). |
| Same classes (9 and 42)? | **Yes.** It sells SaaS to the same kind of buyer (engineering and ops leaders at larger companies). A trademark owner with that traction could object to a "Mendo" tech-debt SaaS. ⚠️ Only an attorney can say how likely. | ⚠️ Unknown until the registers are searched. |
| Marks found | None for "Mendo" itself in the search. Only unrelated "MEND" marks on Justia (security software, case-management SaaS). ⚠️ "MEND" vs "Mendo" is a similarity question for the attorney. | None found. FragMob (sales app, 2015 filings per the roadmap, press release from 2014). ⚠️ One letter apart in pronunciation, both mobile or software goods. Check that FragMob is still live. |
| Search-engine collision | Heavy. "Mendo" the company will outrank a new product for years. | Light. |

Sources: [Goodwin press release](https://www.goodwinlaw.com/en/news-and-events/news/2026/06/announcements-technology-mendo-raises-12-million-series-a-funding),
[Pulse 2.0](https://pulse2.com/mendo-raises-e12-million-series-a-to-accelerate-enterprise-genai-adoption/amp/),
[Startuprise](https://startuprise.co.uk/mendo-raises-e12-mn-in-series-a-round-led-by-ventech-and-educapital/),
[Caplight profile](https://www.caplight.com/company/mendo) (lists `mendo.cloud`),
[Justia "MEND"](https://trademark.justia.com/975/77/mend-97577085.html),
[Fragmob press release](https://www.globenewswire.com/news-release/2014/12/19/1175761/0/en/Direct-Selling-Goes-Digital-With-Fragmob-Mobile-Apps.html).
A search for "Paydown" or "Mora" plus technical debt found no product with either name, but
Paydown is a generic finance word and `paydown.com` has been held since 2001.

### 2.4 Summary scorecard

Scale: good / mixed / poor. This is judgement, not measurement.

| Criterion | Mendo | Fragmo | Paydown | Mora |
|---|---|---|---|---|
| Domains (`.com` plus one good `.dev` / `.app` / `get` / `hq`) | poor (all six taken) | mixed (`.com` taken and probably for sale; `.dev`, `getfragmo.com`, `fragmohq.com` free; `.app` taken) | mixed (`.com` taken; `.dev` free) | poor |
| Package and handle names | good | good (GitHub unverified) | poor (npm taken) | poor |
| Trademark and existing-product risk | **poor** (funded same-class SaaS) | mixed (FragMob; unknown registers) | mixed (descriptive word) | poor (common word) |
| Pronounceable and spellable across languages | good | mixed ("Phragmo" spelling, "frag" word) | mixed (English-centric) | good |
| Memorable on first hearing | good | good (odd and distinct) | mixed | mixed |
| Fit with the technical-debt positioning | good (mend your debt) | mixed (gatekeeper fits PR checks, less the tracking and digests) | good (explains itself) | mixed |

## 3. Recommendation, with reasoning

Written as a product-first founder would see it: what a stranger hears, and what it costs to
own the name. The maintainer decides.

**1. Mendo: do not use it.** On meaning alone it is the best name in the list. "Mend your tech
debt" fits the positioning, it is easy to say in most languages, and it sounds friendly. But
the research found that the name is already a funded, growing B2B SaaS brand, with its own
domain (`mendo.cloud`) and a June 2026 Series A. That is a bigger problem than it first looks:

- **Trademark.** A company of that size will have, or soon have, registrations in classes 9
  and 42, and will defend them. The roadmap's own note "No developer tool found with this name"
  is true, but it does not cover a different SaaS sold to the same companies.
- **Findability.** You would be the second "Mendo" for search engines, app stores and
  press, and any buyer who hears the name will think of the first one.
- **Domains.** `.com`, `.dev`, `.app`, `getmendo.com` and `mendohq.com` are all registered.
  `mendo.io` is unverified.
- **Phase 3 working name.** `mendo-cloud` is almost the same string as their website. Even
  as a private repo name it is confusing; rename it when the final name is chosen.
- **Japanese.** *mendō* (面倒, "hassle") remains a point for the language check, but it is no
  longer the main reason.

**2. Fragmo: provisional choice, conditional on the human checks.**

- *Pronounceability.* Two syllables, written as it sounds. Possible friction: the
  "phragmosis" spelling ("Phragmo"), and the "fr-ag-mo" cluster for Hindi and Tamil speakers
  (⚠️ untested, the language check will say). The word "frag" is a verb in gaming slang
  ("kill") and *Frage* ("question") and *frag!* ("ask!") are German words (⚠️ from general
  knowledge, not verified in this run). Neither is a bad meaning for a code-health tool, but they
  are noise the German speaker should be asked about.
- *Memorability.* Strong because it is odd. It has a real origin story (ant soldiers that
  plug the nest entrance with their heads), which makes a good founder anecdote and logo idea.
  The cost: the name means nothing until the story is told, so the tagline must do the work.
- *Fit with technical debt.* Good for the PR check and merge gate ("stop debt at the door"),
  which is the sharpest hook, and it suits a **gatekeeper** story. It is weaker for the
  tracking, ownership and digest parts, and it says nothing about "debt". The tagline has to
  carry "technical debt" explicitly. This is the main product reason to run the recall test
  against Paydown as a control.
- *Availability.* The best of the four. No product found, PyPI and npm free, `fragmo.dev`,
  `getfragmo.com` and `fragmohq.com` look free. `fragmo.com` is held and probably listed for
  sale (price unknown). `fragmo.app` was registered two months ago by someone unknown.
  Use `fragmo.dev` or `getfragmo.com` as the main address if you do not want to buy `.com`.
- *Trademark risk.* Medium and unknown. The nearest risk is FragMob (class 9 and similar
  goods, pronounced almost the same). It needs the register searches and the attorney check.
- *The "frag" risk.* The roadmap flags this and it is real. A developer audience will get the
  gaming meaning instantly, and some engineering managers (the buyer in 2.1) may read it as
  aggressive. The recall test and the language check are the proper way to see whether it hurts.

**3. Fallback: Paydown.** It explains the product in one word to English speakers, and the
`.com` has been held since 2001, so budget for a different TLD (`paydown.dev` looks free) or a
brand-adjacent address (`getpaydown.com`, unchecked). Weaknesses: npm name taken, descriptive (harder
to protect), and English-centric. It is a good fallback if Fragmo fails the human checks.

**4. Drop Mora.** All of `.com`, `.dev` and `.app` are registered, and both PyPI and npm names
are taken. It is a common word in several languages, which makes trademark and search
collisions likely.

**What would change this recommendation:**

- The trademark check finds a live FragMob (or similar) registration in class 9 or 42 that
  an attorney considers confusingly close. Then fall back to Paydown, or open a new shortlist.
- Fewer than 3 of 5 developers recall "Fragmo" and roughly what it does (section 7).
- A speaker in the language check reports an offensive or off-putting meaning that was not
  found here.
- `fragmo.com` turns out to be cheap enough, or the `.app` owner turns out to be a competitor.

## 4. Tagline candidates

One line, tech debt first, with TODOs as the first proof point (D6). ⚠️ These are untested copy.

For **Fragmo** (leads with the gatekeeper story):

1. "Stop tech debt at the door."
2. "The gatekeeper for your codebase."
3. "Every TODO gets an owner and a deadline. Debt that doesn't get past the gate."
4. "Track your technical debt before it tracks you." (from 2.1, name-independent)

For **Mendo** (only if it is somehow still chosen): "Mend your tech debt."

For **Paydown**: "Pay down your tech debt, one TODO at a time."

Use the recall test (section 7) to compare candidate 1 against candidate 4 with the same name.

## 5. Trademark search kit (maintainer)

> **This is not legal clearance.** A search of public registers finds exact and similar marks;
> it does not tell you whether you can use a name. Before spending money on the brand (domains
> beyond a hold, logo, landing page), ask a trademark attorney or agent to confirm. ⚠️ URLs below
> were not opened from this sandbox, so check that each is still current.

Search both names (and variants: `Mendo`, `Mendoo`, `Mendow`; `Fragmo`, `Phragmo`, `Fragmob`,
`Fragmoo`) in **class 9** (downloadable software) and **class 42** (SaaS, software as a service). Also search
class 35 and 36 only if the tool offers a wide search. Note down: mark, owner, class, status
(live, pending, dead), country, filing date.

| Register | URL | Steps |
|---|---|---|
| IP India | https://ipindiaservices.gov.in/eregister/ (the roadmap's link). Public Search for trade marks is also at https://tmrsearch.ipindia.gov.in/tmrpublicsearch/ ⚠️ unverified | Choose "Wordmark". Type the name. Search "Phonetic" or "Similar" mode if offered. Set class to 9, then repeat for 42. Open each hit with status "Registered", "Pending" or "Objected". |
| USPTO | https://tmsearch.uspto.gov/ | Use "Basic search", search type "contains". Enter the name. Add the filter "International class 009" then "042". Include live and dead marks and look at status. Repeat with the variants. |
| WIPO Global Brand Database | https://branddb.wipo.int/ | Tab "Brand". Brand name field: the name. Use "Nice class" 9, then 42. It covers many countries, including some national registers. |
| EUIPO TMview (extra, because the Mendo company is French) | https://www.tmdn.org/tmview/ | Search the name; filter classes 9 and 42; check EUIPO and France (INPI). |

Record the results in the table below and share it with the attorney.

| Name | Register | Class | Mark found | Owner | Status | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |

## 6. Language check kit

Goal: at least **5 people** with different first languages: Hindi, Tamil, Spanish, Japanese,
German (one per language). Ask the same names (Fragmo, plus Mendo and Paydown if you want
a control). Do it one person at a time so they do not influence each other. 5 minutes each.

**Script**

1. Show the written name on a card or screen. Do not say it. "Please read this word aloud."
   Write down how they said it (a rough phonetic spelling). → question **(a)**.
2. Take the card away. Say the name once, clearly. "Please write it down the way you would spell it."
   Write down what they wrote. → question **(b)**.
3. "Does this word mean anything to you in your language, or sound like a word you know? Does it
   sound rude, funny, scary or odd?" Write down any word they name. → question **(c)**.
4. Optional, last: "What kind of product would you guess has this name?" (Do this last so it does not bias the first three answers.)

**Form (one per person)**

| Field | Answer |
|---|---|
| Name tested | |
| First language, country | |
| (a) How they read it aloud (phonetic) | |
| (a) Hesitated? (y/n) | |
| (b) How they spelled it after hearing it | |
| (b) Matches the real spelling? (y/n) | |
| (c) Bad, rude or unusual meaning? What word? | |
| (c) Sounds like another word? Which? | |
| Optional: what product they guess | |
| Overall: fine / minor concern / blocker | |

**Results table**

| Language | Person (initials) | (a) read aloud | (b) spelled | (c) meaning or concern | Verdict |
|---|---|---|---|---|---|
| Hindi | | | | | |
| Tamil | | | | | |
| Spanish | | | | | |
| Japanese | | | | | |
| German | | | | | |

**Known points to listen for** (⚠️ from general knowledge, not checked with native speakers):

- **Mendo, Japanese:** *mendō* (面倒) means "hassle" or "trouble", and *mendōkusai* means
  "a pain, tiresome". It could be an in-joke (tech debt *is* a hassle) or a negative. Ask the
  Japanese speaker which it is.
- **Fragmo, German:** "frag" is the imperative of *fragen* ("ask"), and *Frage* is "question".
  Ask whether it reads as a word or as an unfinished sound.
- **Fragmo, general:** the gaming verb "to frag" (kill), and the link to *fragment* / *fragile*
  / Spanish *frágil* and *fragmento*.
- **Mendo, Spanish:** the surname/place-name family (Mendoza, Mendo) may sound like a person's
  name.
- **Spelling:** does anyone write "Phragmo", "Fragmow" or "Fragmoh"?

**Pass rule** (⚠️ rule of thumb, not sourced): at least 4 of 5 read it without hesitating
and nobody reports a blocker. A "minor concern" is fine if it is just a funny association.

## 7. Recall test kit

Goal: see whether the name and the one-line promise stick. Use **5 developers** (not the same
people as the language check) who do not already know the project.

**Script**

1. Day 0. In a short call or chat, say: "I'm building a tool called **Fragmo**. It's
   *<tagline>*." Say it **once**. Do not repeat it, spell it or write it down. Then talk about
   something else for a few minutes. (For a side-by-side, give another group of 5 the
   other name and tagline: same script.)
2. Day 1 (about 24 hours later), message them: "Yesterday I told you about a tool. What was it called,
   and what does it do?" Do not give hints.
3. Record the exact words. Then ask: "How would you spell it?" and "Would you remember it in a
   month?" (yes / maybe / no).

**Results table**

| # | Name tested + tagline | Role | Recalled name? (exact / close / no) | Spelled it | What it does (their words) | Roughly correct? (y/n) | Month memory |
|---|---|---|---|---|---|---|---|
| 1 | | | | | | | |
| 2 | | | | | | | |
| 3 | | | | | | | |
| 4 | | | | | | | |
| 5 | | | | | | | |

**Pass criterion** (⚠️ rule of thumb, not a benchmark): **at least 3 of 5** recall the name
(exact or one letter off) **and** roughly what it does (tracks or blocks tech debt or TODOs). 5 people is
too few to prove anything; treat the result as a warning, not as statistics. If one name and
tagline beats the other by 2 or more people, prefer it.

## 8. Remaining maintainer steps, in order

1. **Look at the Mendo finding** and decide whether to drop Mendo (recommended). If yes, tell
   the next agent, and plan to rename the `mendo-cloud` working name (Phase 3).
2. **Check the manual handles** for Fragmo (and Paydown): GitHub user and org, X, LinkedIn,
   GitHub Marketplace (URLs in section 2.2). Also check `fragmo.io` in a registrar search.
3. **Look at what is on** `fragmo.com` (for sale?), and `fragmo.app` (live product?). Note
   the asking prices in the table in section 2.1.
4. **Run the trademark searches** (section 5) for Fragmo, with FragMob in particular. Save the
   results in the table.
5. **Run the language check** (section 6) with 5 people.
6. **Run the recall test** (section 7) with 5 developers, ideally Fragmo against Paydown.
7. **Book a trademark attorney or agent** (India first, plus the US or EU if you plan to sell
   there) and send them the results. Do this before buying anything beyond a single domain.
8. **Choose the name**, then fill in "Domains and handles registered" and "Final decision" below.
9. **Only then** replace the "Mendo" placeholder across `roadmap/` (README D6, phase files,
   `mendo-cloud` in Phase 3), mark D6 as ✅ in `roadmap/README.md`, and start 2.1.

## 9. Domains and handles registered

_To be filled in by the maintainer after buying or reserving. Nothing has been bought._

| Item | Name | Registrar or platform | Date | Cost (INR) | Notes |
|---|---|---|---|---|---|
| Primary domain | | | | | |
| Secondary domains | | | | | |
| GitHub org | | | | | |
| PyPI / npm name | | | | | |
| X | | | | | |
| LinkedIn | | | | | |

## 10. Final decision

_To be filled in by the maintainer._

- **Chosen name:**
- **Tagline:**
- **Date:**
- **Reasons / what the checks showed:**
- **Trademark attorney outcome:**
- **Placeholder "Mendo" replaced across `roadmap/`:** no / yes (date)
