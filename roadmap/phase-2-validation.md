# Phase 2: SaaS validation

**Goal:** find out, cheaply, whether teams will **pay** for hosted TODO and technical-debt
tracking before writing any SaaS code.

⚠️ Effort: low (a few days of work), but it takes 4 to 6 weeks of elapsed time to collect a
signal. 2.1 and 2.2 can start **now**, in parallel with Phases 0 and 1.

**Exit criteria:** a written GO / NO-GO decision (`roadmap/decision-saas.md`) backed by
interview notes and the metrics from 1.5.

Read [README.md](README.md) first for the dependency graph and open decisions.

---

## 2.1 Landing page and waitlist

**Size:** S · **Hard dependencies:** none · **Soft dependency:** D6 (name and domain) · **Feeds:** 1.5 and 2.3

### Scope
1. A one-page site, separate from the docs, aimed at **engineering managers and tech leads**,
   not individual developers:
   - **headline:** e.g. "See every overdue TODO across your GitHub org. Get a weekly digest
     in Slack.";
   - three benefits: owner and age tracking, weekly digests per person, PR checks;
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
