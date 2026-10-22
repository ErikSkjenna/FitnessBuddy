# Customer smoke test: do people want a workout partner?

This is separate from software smoke testing. Passing the automated tests shows the prototype's basic flows work. It does not prove that people will use the product.

## Starting evidence

The supplied presentation proposes connecting fitness-minded people and organizing meetups. Its validation and traction slides are still placeholders. The three supplied interviews suggest:

- Schedule alignment and consistency can make finding a partner difficult.
- Some beginners value company while getting comfortable at the gym.
- Experienced exercisers may be content exercising alone.

Treat these as hypotheses from a small qualitative sample. The app's sample profiles are invented and do not represent the interviewees.

## Hypothesis

Among beginners or people trying to build a consistent routine, enough participants will choose a compatible workout time and request a real pilot session to justify a small trial.

## Run a small, supervised test

Recruit 10 people from that target group. This is an exploratory sample, not a statistically representative study. Use anonymous IDs P01–P10 in `customer-test-log.csv`.

1. Explain: “This is a student prototype. The people and bookings shown are fictional. We are testing whether the idea would be useful.”
2. Show the page without explaining how to navigate it. Ask what they think it offers.
3. Give this task: “Find someone whose schedule fits yours, then plan a workout you would actually attend.” Record completion without help and any blocker.
4. Ask: “What would stop you from trying this?” Then: “How do you solve this problem today?” Avoid suggesting the answer.
5. Separately ask whether they want to take part in a real pilot. If yes, request a concrete activity and availability. Do not count a fictional Join click as a real commitment.
6. Record interest only with consent. The prototype stores emails locally and sends nothing. A participant may decline email and still give feedback.

Keep the app on your own laptop for these sessions. No public deployment is included. The app has one shared profile; participants should edit it in turn. Record participant-level observations manually because the app does not measure distinct visitors or click conversion.

## Decide thresholds before recruiting

Illustrative thresholds you can change BEFORE testing:

| Measure | How to calculate | Initial decision threshold |
| --- | --- | --- |
| Basic usability | Number completing partner search and a demo meetup without help / 10 | At least 8/10 |
| Expressed pilot interest | Number explicitly requesting a future pilot / 10 | At least 4/10 |
| Concrete intent | Number offering a usable activity and time for a real pilot / 10 | At least 3/10 |

These are team decision rules, not industry benchmarks. Report counts and recruitment context, not just percentages. Mixed results may mean narrowing the audience or simplifying the flow. A good signal justifies a small real pilot, not a claim of product-market fit.

## Follow-up test after explicit participant agreement

Manually coordinate one public-location session with interested participants. Track confirmations and attendance. Attendance is stronger evidence than “sounds interesting.” The prototype does not send invitations or match real users, so this requires separate coordination by your team.

## Presentation text to fill AFTER testing

“We tested the prototype with ___ participants recruited from ___. ___ completed the main task without assistance. ___ requested a pilot, and ___ supplied a concrete activity and available time. The most common barrier was ___. Based on these results, our next change is ___.”

Do not populate those blanks from software tests, demo profiles, or invented participants. No customer smoke test was conducted as part of this build.
