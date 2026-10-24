# Interview notes template

Copy this file to `roadmap/interviews/notes/INT-NNN.md` (one file per interview, NNN = a running number) and fill it in during or right after the
call, within 24 hours. The block between the two `---` lines is read by `scripts/tally_interviews.py`, so keep it as simple `key: value` lines: one
value per line, no quotes, nothing after the value except an optional ` # comment`. Leave a value empty if you do not know it.

⚠️ **Privacy:** use the alias `INT-NNN`. Do not write the person's name, email, employer name, repository names or anything that identifies them in a
note that is committed to the repository. Keep the mapping from alias to person in your private tracking sheet (see the README). Describe the company
by size and kind ("product company, 120 developers"), not by name.

Score **on evidence, not adjectives**: a story with a date and a cost beats "yes, it is a big problem".

## Front matter (copy this block to the top of the note)

```text
---
id: INT-NNN
date: YYYY-MM-DD
interviewer: your initials
source: linkedin             # waitlist | launch-commenter | linkedin | reddit | meetup | referral | other
role: em                     # em | tech-lead | staff | other
company_size: 10-49          # developers: 10-49 | 50-200 | other (write 1-9 or 200+ for out-of-profile interviews)
team_size: 8                 # developers on their team
region: india                # india | apac | emea | americas | other
pain: 3                      # 1 to 5, see the definitions below
recurring: no                # yes | no
would_pay: maybe             # yes | maybe | no
amount_inr: 0                # monthly amount in rupees they named, 0 if none
commitment: none             # none | pilot | pre-order | loi
---
```

Add `example: true` to the front matter of any practice or fake note so that the tally skips it. A file name starting with `example` is skipped too.

## Pain intensity (1 to 5)

| Score | Name | What you heard or saw |
|---|---|---|
| 1 | No pain | They do not think about it. No story, no cost. |
| 2 | Mild | They recognise it when asked, but it never cost them anything they can name. No action taken. |
| 3 | Real but tolerated | A concrete annoyance with a workaround (a spreadsheet, a reminder, a lint rule). They have not tried to fix it properly, or tried and stopped. |
| 4 | Painful | A story from the last 6 to 12 months with a cost (a bug, an incident, a missed deadline, hours lost). They talk about it in the team. They have tried or planned a fix. |
| 5 | Severe | It is being worked on now: time, money or a named person is allocated, or it was escalated to leadership. They would act this quarter. |

⚠️ Rule of thumb: count a 4 or 5 only if you wrote down the story that justifies it. "Recurring" means it happened more than once, or keeps happening
(not a single old event).

## Body

### Who they are
- Role and seniority:
- Company size (developers) and kind of company:
- Team size and what the team builds:
- Region:
- Repositories on GitHub (rough number, mono or many repos):

### Current process
How they track tech debt or TODOs today (tools, meetings, tickets, linters, who looks at it, how often):

### Tools tried
What they tried, why it stuck or did not stick, what it cost:

### The last incident caused by a forgotten TODO
When, what happened, who found it, what it cost (hours, money, customer impact), what changed afterwards. If there is no story, write "none" (do not fill in one):

### Who owns the problem, who approves spend
- Owner of the problem (role, not name):
- Who approves spend for a tool like this, and up to which amount without approval:
- Budget cycle or procurement steps they mentioned:

### Landing page reaction
- First reaction, what they said it is (in their words):
- What is missing or unclear:
- What they would use first:

### Willingness to pay
- Amount they expected before seeing the prices (INR per month):
- Reaction to the Team (₹1,499) and Business (₹4,999) anchors: too cheap / about right / too expensive / not for us:
- Answer: yes / maybe / no, and the reason:

### Commitment
What was asked and what they agreed to, with the specific next step (who, what, by when). Count it only if there is a concrete step:
- [ ] Paid pilot
- [ ] Pre-order
- [ ] Letter of intent
- [ ] None (what they said instead):

### Verbatim quotes
Exact words in quotation marks, with a tag for the theme. Anonymise before sharing outside the project (no names, employers or repository names).

- "…" (theme: )
- "…" (theme: )

### Follow-ups
- Thank-you sent: yes / no
- Promised to share findings: yes / no
- Introductions offered (to an approver or a peer), by alias:
- Anything to check or change in the script:
