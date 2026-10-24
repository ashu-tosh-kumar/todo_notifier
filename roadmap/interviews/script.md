# Interview script (25 minutes)

A conversation about **the problem first**. The product, the landing page and the prices come only in the last 5 minutes. The style follows the
"Mom Test": ask about the person's past behaviour and real examples, not about opinions of an idea.

> **⚠️ Do not pitch**
>
> - Do not describe, name or hint at the product before section 6. If they ask "what are you building?", say: "I will show you at the end, I do not
>   want to bias your answers."
> - Do not ask "would you use…", "would it be useful if…" or "do you think a tool should…". They produce polite yes answers that mean nothing.
> - Ask about the **last time** something happened, not what they "usually" or "would" do.
> - Do not fill silences, suggest answers or correct them. Wait 5 seconds, then ask "anything else?".
> - Compliments, general opinions and promises about the future are not evidence. Write down facts: what happened, when, what it cost, what they did.
> - You are not selling. Do not argue, defend the idea or explain how it would solve their problem.

## Before the call

- Send the invite, and say the call is 25 minutes (30 at most).
- Open `notes-template.md` (copied to `notes/INT-NNN.md`). Have the landing page open in a separate window, not shared yet.
- Check the previous interviews' follow-ups. After the first two interviews, change the questions that confused people.

## Timings at a glance

| Minutes | Section |
|---|---|
| 0 to 2 | 1. Intro and consent |
| 2 to 4 | 2. Their world |
| 4 to 8 | 3. How they handle it today |
| 8 to 13 | 4. The last time it hurt |
| 13 to 16 | 5. What they tried |
| 16 to 19 | 6. Ownership and spend |
| 19 to 24 | 7. The landing page, willingness to pay and commitment (only now) |
| 24 to 25 | 8. Wrap-up |

⚠️ Rule of thumb: if you run over, cut the probes in sections 2 and 3 first. Never cut section 4 (the story) or the commitment question in section 7.

## 1. Intro and consent (2 min)

Say, in your own words:

> Thanks for making time. I am researching how engineering teams deal with tech debt, in particular things like TODO comments that get forgotten.
> This is not a sales call and there are no right answers. I am more interested in what really happened than in opinions.
>
> Two things before we start. May I take notes? And may I record the audio so I do not miss anything? The recording stays with me, only I will
> listen to it, and I delete it after I have written up the notes. In what I share, I will not use your name or your company's name. You can skip any
> question or stop at any time.

- ⚠️ If they say no to recording, do not record, and do not ask again. Take notes only.
- Start the recording only after a clear yes, and say that it has started.

## 2. Their world (2 min)

1. Tell me about your role and the team you work with.
   - Probes: How many developers are on your team, and in the company? How many repositories? What do you build?
2. What is on your plate this month, technically and as a manager?

Note: role, company size, team size, region. If they are outside the profile (fewer than 10 or more than 200 developers), still finish the call; it
is useful data.

## 3. How they handle it today (4 min)

3. Walk me through how technical debt, TODOs or "we should fix this later" items are tracked on your team today.
   - Probes: Where do they get written down (code comments, tickets, a document, nowhere)? Who looks at them, and how often? When did you last
     look at the list?
4. Tell me about the last time one of those items was actually picked up and fixed. How did that come about?
   - Probes: Who decided? What triggered it? How long had it been waiting?

If they say "we do not track it", ask: "Tell me about the last time someone said 'we should clean this up'. What happened next?"

## 4. The last time it hurt (5 min)

This is the most important section. Get one specific story, with dates and costs.

5. Tell me about the last time a forgotten TODO, a temporary workaround or a known shortcut caused a bug, an incident or a delay.
   - Probes: When was that? What exactly happened? How was it found, and by whom? How long did it take to fix? What did it cost (hours, a customer,
     a release, money)? What did you change afterwards?
6. And before that? Has something similar happened more than once?
   - Probes: How often in the last year? Is it the same kind of problem each time?
7. If there is no story: "OK. Tell me about the last time tech debt in general slowed your team down. What was it?"

Do not suggest examples. If the answer is "it has never happened", write "none". That is a valid, useful answer.

## 5. What they tried (3 min)

8. What have you tried to get a grip on this? Tell me about the last thing you tried.
   - Probes: Lint rules, ticket labels, a recurring "tech debt Friday", a tool or a script? Who set it up? How much time or money did it cost?
9. Why did it stick, or why did it stop?
   - Probes: What annoyed people about it? What would have made you keep using it? Is it still running today?

If they tried nothing, ask: "Why not? What would have had to be true for you to try something?" Then move on.

## 6. Ownership and spend (3 min)

10. In your team, who feels this problem most? Who actually does something about it?
11. Think about the last tool or subscription your team started paying for. Tell me how that went: who asked for it, who approved it, how long did it
    take, and roughly what did it cost?
    - Probes: Who signs off, and up to what amount can you decide yourself? Does it need a security or procurement review? How do you pay (company
      card, invoice)? What is the budget cycle?
12. Is this problem something you would put on someone's priority list this quarter? Who would decide? (Only if section 4 had a real story.)

## 7. The landing page, willingness to pay and commitment (5 min)

Only now. Say: "Thank you. That was very helpful. Now I will show you something early and rough. It is **not built yet**, it is a page I use to test
whether the idea makes sense. Please be critical."

### 7a. Reaction first (about 1.5 min)

Share the landing page (the brand on it is provisional: call it "the page", not by a pitch). Let them read for 30 seconds without explaining.

13. What do you think this is? In your own words, what does it do?
14. What is missing or unclear? What would you change?
15. Looking at your story from earlier (name it): would this have prevented it, or changed anything? How?

### 7b. Willingness to pay (about 1.5 min)

Ask for the number **before** pointing at the prices, then show the pricing section.

16. If a tool like this existed and worked, what would you expect it to cost your team per month? (Let them name a number.)
17. [Show the pricing sketch: Team, ₹1,499 per month, for one engineering team; Business, ₹4,999 per month, for several teams.] Is the Team price too
    cheap, about right, too expensive, or not something you would consider at any price? And the Business price?
    - Probes: What would make you pay more? What would make it a no? Compared with what you pay for other tools, how does it feel?
18. Tell me about a tool in this area that you pay for today, or that you decided not to pay for. What made the difference?

Write down the number they said first, then their reaction to ₹1,499 and ₹4,999, and the yes / maybe / no with the reason. ⚠️ A number they say
unprompted is worth more than a reaction to your number. Both are weak evidence on their own; the commitment question is stronger.

### 7c. Commitment (about 2 min)

Be honest that nothing can be bought yet. Offer the options, one at a time, and stop at the first one they accept:

19. "If we built this, would you be willing to try it on a real project of yours for a few weeks, as a **paid pilot** at a founding-member price?
    When could that start, and who else would need to agree?"
20. If not: "Would you be willing to **pre-order**, that is, pay or reserve a place before it is finished, at a founding-member price, knowing you
    could get a refund if it does not ship? What would you need to see first?"
21. If not: "Would you sign a short, non-binding **letter of intent** saying that your team intends to buy it, at the price we talked about, if it does
    what you need? Who would sign it?"
22. If none: "What would have to be true for you to say yes? Or is it simply not a problem you would pay for?"

Rules for this section:

- ⚠️ Count a commitment only if the person agrees to a **specific next step** (who, what, by when). "Sounds good, keep me posted" is not a commitment,
  it is a polite "no". Write it down as `none` and quote what they said.
- Do not take a payment, a card number or a signature during the call. Record the willingness and the agreed step in writing, then follow up by
  email with the real next step. Pre-orders and letters of intent need proper wording and, if money is involved, ⚠️ a check of the legal and tax
  rules that apply to you before you accept anything.
- Do not discount, negotiate or promise features to get a yes. A clear "no" is as useful as a "yes".

## 8. Wrap-up (1 min)

23. Is there anyone else I should talk to: a peer, or whoever approves spend on your side? (Ask for an introduction, not a name on the spot.)
24. Is there anything I should have asked and did not?

Then:

- Thank them. Say you will send a short summary of findings (if you promised it) and, for the waitlist people, that they are still on the list.
- Stop the recording. Delete it after you finish the notes (target: within 24 hours of the call).
- Fill in `notes/INT-NNN.md` straight away, while it is fresh. Mark facts and quotes, and keep your interpretation apart in the follow-ups.

## After each interview (2 minutes)

- Did I pitch at any point? If yes, mark the answers after it as biased in the notes.
- Which questions got blank looks or short answers? Fix them before the next call.
- Did I get a story with a date and a cost in section 4? If not, the pain score is probably 3 or lower.
