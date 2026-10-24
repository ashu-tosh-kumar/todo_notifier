# Customer discovery interviews (workstream 2.2)

A kit for 10 to 15 interviews that test whether engineering managers and tech leads feel a tech-debt problem strongly enough to pay for a tool.
The agent drafted the kit. **A human conducts the interviews.** The results feed the GO / NO-GO decision (workstream 2.3,
[phase-2-validation.md](../phase-2-validation.md)).

The product name is provisional (see [decision-name.md](../decision-name.md)). The kit says "the product" or `[Brand]`; only the landing page
carries the working name.

## Who to talk to

- **Role:** engineering managers, tech leads and staff engineers.
- **Company:** 10 to 200 developers, working in GitHub.
- **Region:** India and globally. Aim for a mix, but do not turn down a good interview because of the region.
- **Goal:** **10 to 15 interviews**, 20 to 30 minutes each (the script is 25 minutes).
- Interviews outside the profile (very small or very large companies) are fine as extra data, but do not count them toward the 10.

## Files and the order of use

| Order | File | Use |
|---|---|---|
| 1 | this README | Plan the programme, set up the tracking sheet |
| 2 | [outreach.md](outreach.md) | Send the invitations and the one nudge each |
| 3 | [script.md](script.md) | Run each interview: problem first, landing page, price and commitment at the end |
| 4 | [notes-template.md](notes-template.md) | Copy to `notes/INT-NNN.md` for each interview, within 24 hours of the call |
| 5 | [scripts/tally_interviews.py](scripts/tally_interviews.py) | Count the 2.3 criteria from the notes, at any time |
| 6 | [synthesis-template.md](synthesis-template.md) | When you have 10 or more notes, copy to `synthesis.md` and fill in; link it from `decision-saas.md` (2.3) |

Before the first real interview, practise the script on two friendly engineers and fix what does not work. Practice notes do not count: add
`example: true` to their front matter or do not save them.

## Recruiting sources

From the 2.2 spec, roughly in this order (warmest first):

1. **Personal network on LinkedIn.** Engineering managers and tech leads you know, and people they introduce. Warm contacts reply most often.
2. **Waitlist signups** from the landing page ([landing-page/README.md](../landing-page/README.md)), those who answered "yes" or "maybe" to paying first.
   ⚠️ The form has no "may we contact you for an interview" box. Email each person once, say you are writing because they signed up, make it
   optional and honour a "no" at once. Consider adding a checkbox to the form before launch.
3. **Launch commenters** (Show HN, Reddit, LinkedIn, newsletters; see [../launch/](../launch/)). Reply in the thread, then continue in private.
4. **r/developersIndia** and local **Python or DevOps meetups**. Read the rules first and post once.
5. **Referrals** at the end of every interview ("who else should I talk to?").

⚠️ Rule of thumb: friends and fans of the open-source tool say nicer things than strangers. Aim for at least half of the interviews with people who
do not know you or the project, and note the source of each interview.

## Weekly cadence

| Week | Do |
|---|---|
| 0 | Set up the tracking sheet. Practise the script twice. Decide how you will schedule calls. |
| 1 | Send about 15 to 20 first messages (network and waitlist). Aim for 2 to 3 interviews. |
| 2 | Send the nudges to week 1. Send about 15 more messages (launch commenters, communities). Aim for 3 to 4 interviews. Fill in notes the same day. |
| 3 | Same again. Read the first 6 to 8 notes and tally them. Fix the script. Ask for referrals. |
| 4 | Fill gaps (missing regions, roles, company sizes). Reach 10 to 15 interviews. |
| 5 | Run the tally, write `synthesis.md`, hand over to 2.3. |

⚠️ These numbers are rules of thumb, not benchmarks. Cold replies are usually low (a few in a hundred is common), so plan the volume accordingly. Stop
when you reach 10 solid interviews and hear the same things repeatedly, or at 15.

## Tracking table

Keep this table **outside the repository** (a private spreadsheet), because it holds personal data. Use the alias to link a row to `notes/INT-NNN.md`.

| Alias | Name or alias | Source | Date contacted | Status | Nudge sent | Interview date | Notes file |
|---|---|---|---|---|---|---|---|
| C-001 | e.g. A. Rao (private) | linkedin | 2026-11-02 | contacted | no | | |
| C-002 | | waitlist | | to-contact | | | |

Statuses: `to-contact`, `contacted`, `nudged`, `scheduled`, `done`, `declined`, `no-reply`. After the nudge, mark `no-reply` and stop. When you
schedule an interview, give it the next `INT-NNN` alias. Outside the repository, keep the link between that alias and the person; the notes keep
only the alias.

## Consent and privacy

- **Ask before recording.** The script has the wording. If the answer is no, take notes only. Record audio only (no video), keep the file on your
  own device, and delete it once the notes are written (target: within 24 hours).
- **Collect only what you need.** The notes need the role, company size, team size, region and the story. They do not need a name, an email, an
  employer's name or repository names. The alias `INT-NNN` replaces them.
- **Anonymise quotes.** Remove names, employers, product names and anything that could identify a person or team before a quote leaves the notes
  (in the synthesis, in a blog post, in the decision document).
- **Tell people what happens with the data.** The script's intro says: notes, an anonymised summary, the recording deleted. Keep the promise.
- **Commit only anonymised notes.** If a note cannot be anonymised well enough, keep it local; the tally reads any folder (`--notes-dir`).
- Contact details of waitlist signups and others stay in the private tracking sheet. Delete a person's data if they ask.
- ⚠️ This is a practical guide, not legal advice. Check the rules that apply to you (for example India's DPDP Act for Indian contacts and the GDPR for
  EU contacts) before you collect or keep personal data.

## Counting what the GO decision needs

The tally reads the `key: value` block at the top of every note in `notes/` and prints the counts that 2.3 asks for.

```bash
python roadmap/interviews/scripts/tally_interviews.py                     # real notes only
python roadmap/interviews/scripts/tally_interviews.py --include-examples  # also the FAKE EXAMPLE note
python roadmap/interviews/scripts/tally_interviews.py --notes-dir ~/private-notes
```

| 2.3 criterion (rules of thumb, adjust to your goals) | Threshold | In the tally |
|---|---|---|
| Teams that say they would pay, or commit to a paid pilot, pre-order or LOI | 5 or more | "Would pay (yes) or commit" |
| Interviewees who rate the pain 4/5 or higher and describe a recurring problem | 3 or more | "Pain >= 4 and a recurring problem" |

The waitlist and Action usage criteria do not come from the interviews. The tally also prints region and company-size breakdowns, so you can see
whether the evidence comes from one corner of the market.

⚠️ Count one interview per team. A "yes" without a concrete next step is a "maybe", and a "maybe" does not count toward the 5.

`notes/example-fake.md` is a clearly marked fake example. The tally skips it (and any file whose name starts with `example` or whose front matter has
`example: true`) unless you pass `--include-examples`.

## What to do with the results

1. Run the tally and fill in [synthesis-template.md](synthesis-template.md) as `synthesis.md` (themes with counts and quotes, pains ranked by
   frequency × intensity, willingness to pay, the mapping to the GO criteria and the PIVOT signals).
2. Link it from `roadmap/decision-saas.md` (2.3). The maintainer decides; the synthesis is the evidence, not the decision.
3. Tell the people who asked what you found, and thank everyone who helped.
