# Phase 2: SaaS validation

**Goal:** find out, cheaply, whether teams will **pay** for hosted TODO and technical-debt
tracking before writing any SaaS code.

⚠️ Effort: low (a few days of work), but it takes 4 to 6 weeks of elapsed time to collect a
signal. 2.0 and 2.2 can start **now**, in parallel with Phases 0 and 1. 2.1 follows as soon as
2.0 settles the name.

**Exit criteria:** a written GO / NO-GO decision (`roadmap/decision-saas.md`) backed by
interview notes and the metrics from 1.5.

Read [README.md](README.md) first for the dependency graph and open decisions.

---

## 2.0 Name and brand checks

**Size:** S (an agent researches; the maintainer decides and buys) · **Hard dependencies:** none · **Blocks:** 2.1

**Brief (D6):** the SaaS is positioned as a generic **technical debt tracking tool** that
starts with TODO comments. The name must be unique, simple, easy to pronounce and spell in any
language, and memorable on first hearing. The library keeps the name `todonotifier`.

### Shortlist
Ranked. Quick web checks were done on 2026-10-23. ⚠️ They are not trademark or domain
clearance.

| Rank | Name | Story / tagline | Strengths | Risks found |
|---|---|---|---|---|
| 1 (working name) | **Mendo** | *mend* + *do*: "Mend your tech debt." | Invented word, 2 syllables, spelled as said in most languages, sounds like a friendly brand. No developer tool found with this name. | Japanese *mendō* (面倒) means "hassle". That could work as an in-joke (tech debt *is* a hassle), but test it with Japanese speakers. A small Android publisher "Mendo Company" exists in an unrelated field. |
| 2 | **Paydown** | Finance term for repaying debt: "Pay down your tech debt." | Instantly explains the product to English speakers. No software product found with the name. | Descriptive, so harder to trademark. English-centric. A compound word is weaker on "spell in any language". |
| 3 | **Mora** | Latin and Romance-language term for late payment or default (debt "in mora"). | 4 letters, pronounced the same nearly everywhere, a strong story for overdue debt. No developer tool found with the name. | A common word in several languages (it also means blackberry in Spanish), so `.com` and trademarks are likely crowded. It needs a modifier such as `getmora` or `mora.dev`. |

**Ruled out:** **Kodo** (too close to Kodus, an existing AI code-quality and tech-debt tool),
**Fixa** (fixa.dev, an AI coding agent, already exists), **Duely** (an existing legal-tech
startup, and easily confused with "duly"), **Cruft** (clashes with the `cruft` Python package
for cookiecutter templates), and **Pendo** (an established product analytics company).

### Scope
For each shortlisted name, in rank order, stop at the first name that passes every check:
1. **Trademark:** search classes 9 (software) and 42 (SaaS) in
   [IP India public search](https://ipindiaservices.gov.in/eregister/), the USPTO and the
   WIPO Global Brand Database. Record exact and similar marks. ⚠️ Before spending money on
   the brand, get a trademark attorney or agent to confirm.
2. **Domains:** check `.com`, `.dev`, `.io` and `.app`, plus `get<name>.com` and
   `<name>hq.com`. Note the prices in INR.
3. **Handles:** GitHub organization, PyPI and npm package names, X, LinkedIn page, and the
   GitHub Marketplace listing name.
4. **Language check:** ask at least 5 people with different first languages (for example
   Hindi, Tamil, Spanish, Japanese, German) to (a) say the name after reading it, (b) spell
   it after hearing it, and (c) report any bad meanings.
5. **Recall test:** say the name and tagline once to 5 developers and ask them a day later
   what it was called and what it does.

### Deliverable
`roadmap/decision-name.md`: the chosen name, the evidence from each check, the domains and
handles registered (by the maintainer), and a one-line tagline. Then replace the "Mendo"
placeholder across `roadmap/`.

---

## 2.1 Landing page and waitlist

**Size:** S · **Hard dependencies:** 2.0 (name and domain) · **Feeds:** 1.5 and 2.3

### Scope
1. A one-page site, separate from the docs, aimed at **engineering managers and tech leads**,
   not individual developers:
   - **headline** (tech-debt positioning, TODOs as the first proof point): e.g. "Track your
     technical debt before it tracks you. Start with every TODO across your GitHub org, with
     owners, deadlines and a weekly Slack digest.";
   - three benefits: owner and age tracking, weekly digests per person, PR checks. Add a
     "coming next" line listing other debt sources (lint suppressions, skipped tests,
     outdated dependencies), and use the waitlist form to ask which one people want most;
   - a mock dashboard screenshot (it can be a static design);
   - a **pricing sketch** to test willingness to pay (⚠️ illustrative numbers, to be tested):
     Free (1 repo), Team at about ₹1,499/month, Business at about ₹4,999/month, with "join the
     waitlist for founding-member pricing";
   - a waitlist form asking for email, company size, number of repos, current tool and
     "Would you pay for this? (yes / maybe / no)".
2. **Stack** (choose the cheapest that works): static HTML on GitHub Pages or Cloudflare
   Pages, plus a form tool (e.g. Tally or Google Forms). Use privacy-friendly analytics
   (e.g. Plausible or a self-hosted Umami ⚠️; check current pricing).
3. **Link it** from the README ("Team dashboard coming soon: join the waitlist"), the docs and
   the Action README.
4. Make sure the page is honest: it says the product is not built yet and the waitlist is for
   early access.

### Acceptance criteria
- The page is live before 1.5 launches, signups arrive in a sheet the maintainer can see, and
  analytics record visits by source.

---

## 2.2 Customer discovery interviews

**Size:** M (a human conducts the interviews; an agent drafts and synthesizes) · **Hard dependencies:** none · **Soft dependency:** 2.1 (as a recruiting source) · **Feeds:** 2.3

### Scope
1. **Target:** engineering managers, tech leads and staff engineers at companies with
   10 to 200 developers on GitHub, in India and globally. Aim for **10 to 15 interviews** of
   20 to 30 minutes each.
2. **Recruiting:** waitlist signups, launch commenters, LinkedIn (personal network first),
   r/developersIndia and local Python or DevOps meetups.
3. **The agent drafts:**
   - an outreach message (short, no pitch: "researching how teams handle tech debt");
   - an interview script focused on the **problem first**, the solution later. For example:
     - How do you track tech debt or TODOs today?
     - When did a forgotten TODO last cause a bug or incident?
     - Who cares about this in your team? Who would approve paying for a tool?
     - What have you tried? Why did it stick or not stick?
     - (Last) Show the landing page: what is missing? Would you pay ₹X/month?
   - a notes template (role, company size, current process, pain intensity 1–5,
     willingness to pay, quotes).
4. **Synthesis:** the agent groups the notes into themes with counts and direct quotes, and
   ranks pains by frequency and intensity. The `product-management:synthesize-research`
   skill can help with this step.

### Acceptance criteria
- At least 10 interviews completed with notes in the template.
- A synthesis document with themes, counts and quotes, linked from `decision-saas.md`.

---

## 2.3 GO / NO-GO decision

**Size:** S (the maintainer decides) · **Hard dependencies:** 1.5, 2.1, 2.2 · **Blocks:** Phase 3

### Inputs
- Metrics from `roadmap/metrics.md` (downloads, stars, Action usage, waitlist signups and
  conversion).
- The interview synthesis from 2.2.

### Suggested GO criteria
⚠️ These are rules of thumb, not sourced benchmarks. Adjust them to your goals.

| Signal | GO threshold |
|---|---|
| Teams that say they would pay (or commit to a paid pilot, pre-order or letter of intent) | 5 or more |
| Waitlist signups | 100 or more, with 20% or more answering "yes" to paying |
| Interviewees who rate the pain 4/5 or higher and describe a recurring problem | 3 or more |
| Repos using the GitHub Action ("Used by" plus Marketplace) | 20 or more |

### Outcomes
- **GO:** start Phase 3. Offer founding-member pricing to the interested teams and recruit
  3 to 5 design partners.
- **PIVOT:** if the pain is real but about something adjacent (for example general tech-debt
  visibility, or ownership of stale code), rewrite the Phase 3 scope before building.
- **NO-GO:** keep the open-source project healthy, use it as a portfolio piece and revisit in
  6 months. Optional low-cost revenue: GitHub Sponsors (already configured in
  `.github/FUNDING.yml`).

### Deliverable
`roadmap/decision-saas.md`: the decision, the evidence, and the Phase 3 scope changes, if any.
