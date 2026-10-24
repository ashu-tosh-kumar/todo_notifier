# SaaS GO / NO-GO decision

**Status:** ⬜ Not decided. Fill this in 4 to 6 weeks after the launch (1.5). The decision is the
maintainer's. This file is the template from workstream [2.3](phase-2-validation.md#23-go--no-go-decision).

| Field | Value |
|---|---|
| Decision date | |
| Decision | GO / PIVOT / NO-GO |
| Decided by | |
| Launch date (1.5) | |
| Weeks of data | |

## 1. Inputs

| Input | Where | Ready? |
|---|---|---|
| Launch and adoption metrics | [metrics.md](metrics.md), weekly table | ⬜ |
| Waitlist export | The sheet behind the landing page form ([landing-page/README.md](landing-page/README.md)) | ⬜ |
| Interview notes | `interviews/notes/*.md` ([interviews/README.md](interviews/README.md)) | ⬜ |
| Interview tally | `python roadmap/interviews/scripts/tally_interviews.py` | ⬜ |
| Interview synthesis | Copy of [interviews/synthesis-template.md](interviews/synthesis-template.md), filled in | ⬜ |
| Brand decision | [decision-name.md](decision-name.md) | ⬜ |

## 2. Evidence against the GO criteria

⚠️ The thresholds come from [phase-2-validation.md](phase-2-validation.md#23-go--no-go-decision).
They are rules of thumb, not sourced benchmarks. If you change one, write the new value and the
reason in the "Threshold used" column before you fill in the "Actual" column, not after.

| Signal | Suggested GO threshold | Threshold used | Actual | Met? | Source |
|---|---|---|---|---|---|
| Teams that say they would pay, or commit to a paid pilot, pre-order or LOI | 5 or more | | | | Tally: "Would pay (yes) or commit" |
| Waitlist signups | 100 or more | | | | Waitlist sheet |
| Share of signups answering "yes" to paying | 20% or more | | | | Waitlist sheet |
| Interviewees rating the pain 4/5 or higher and describing a recurring problem | 3 or more | | | | Tally: "Pain >= 4 and a recurring problem" |
| Repos using the GitHub Action ("Used by" plus Marketplace) | 20 or more | | | | metrics.md, latest week |

**Criteria met:** _ of 5.

Supporting context (not criteria, but read them):

| Context | Value |
|---|---|
| PyPI downloads per week, baseline → latest (without mirrors) | |
| GitHub stars, baseline → latest | |
| Signups by source (UTM): top 3 | |
| Most-requested next debt source (waitlist checkbox) | |
| Strongest quote for building | |
| Strongest quote against building | |

## 3. Reading the evidence

Guidance only. The maintainer can overrule it, but should write down why.

- **GO:** most criteria are met, and the commitment criterion (paid pilot, pre-order or LOI) is
  one of them. Stated willingness to pay without a commitment is the weakest signal, so do not
  call GO on survey answers alone.
- **PIVOT:** the pain is real (the pain and interview criteria are met) but it is about something
  adjacent, such as general technical-debt visibility or ownership of stale code, or the waitlist
  asks for a different debt source than TODOs. Rewrite the Phase 3 scope before building.
- **NO-GO:** the pain and commitment criteria are not met. Keep the open-source project healthy
  and revisit in 6 months.

## 4. Decision and reasoning

_Write 5 to 10 sentences: what was decided, which evidence carried it, what would have changed
the decision, and the biggest risk you accept._

## 5. Consequences

### If GO
- [ ] Offer founding-member pricing to the teams that committed.
- [ ] Recruit 3 to 5 design partners, with names and dates.
- [ ] Confirm the brand ([decision-name.md](decision-name.md)) and create the private
      `<brand>-cloud` repo (D3).
- [ ] Phase 3 scope changes, if any, listed below, and [phase-3-saas-mvp.md](phase-3-saas-mvp.md)
      updated to match.

### If PIVOT
- [ ] The new problem statement, in one sentence.
- [ ] The Phase 3 scope rewritten before any code.
- [ ] The interviews or landing-page test to run next, with a new decision date.

### If NO-GO
- [ ] Note the reason in the main README roadmap section (optional).
- [ ] Keep the library maintained: Dependabot, releases, issues.
- [ ] Optional low-cost revenue: GitHub Sponsors (`.github/FUNDING.yml` is already set up).
- [ ] Revisit date (6 months from now):

## 6. Phase 3 scope changes

_None yet._
