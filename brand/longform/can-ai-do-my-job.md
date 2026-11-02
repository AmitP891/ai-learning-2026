# Long-form: Can AI do my job? An aerospace engineer tests Claude

Target: January (after the capstone). 16:9, about 10 minutes, plus one Short per task. Idea #65.

## Ground rules (non-negotiable)
- **Synthetic data only.** Every input is invented for this video: a fictional system, made-up numbers. Nothing from work, no real programmes, suppliers or customers.
- **Check with work first** that a public video about AI and systems engineering tasks is fine, even with synthetic data.
- **I mark it, not Claude.** I'm the domain expert; Claude's self-score is shown but doesn't count.
- **Same prompt style for every task**: the input, one paragraph of context, the output format. No retries unless the task says so.

## The fictional system
A small **flight data logger** for a light aircraft (same as the requirements sample, so it ties to earlier videos): records GPS, altitude and engine data, stores 72 hours, downloads over a cable.

## The 5 tasks (a normal week for a systems engineer)

| # | Task | Input I give | What "good" looks like |
|---|---|---|---|
| 1 | **Review requirements** | 15 requirements, 6 with deliberate flaws | Finds all 6, no false alarms, rewrites are testable |
| 2 | **Write verification test cases** | 5 good requirements | One test per requirement, measurable pass/fail, right method (test, analysis, inspection, demonstration) |
| 3 | **Run a trade study** | 3 fictional GPS modules with specs and costs, my 5 criteria | Sensible weights, correct maths, a justified pick, flags missing data |
| 4 | **Draft an interface definition** | System description of logger + 3 connected units | Complete interface list, signals, directions, nothing invented |
| 5 | **FMEA on one subsystem** | Power supply description | Credible failure modes, effects, causes; sensible severity; no made-up failure rates presented as fact |

## Scoring (per task, out of 10)
| Criterion | Points | Question |
|---|---|---|
| Correct | 4 | Is it technically right? |
| Complete | 2 | Did it miss anything a reviewer would catch? |
| Honest | 2 | Did it flag assumptions instead of inventing facts? |
| Usable | 2 | Could it go into a design review with light edits? |

Also record **time**: how long Claude took vs my estimate of doing it by hand.

## The verdict scale (decided only after the scores)
- **8–10 average**: "It could do this part of my job."
- **5–7**: "A fast junior engineer who needs checking."
- **Below 5**: "Not yet."

## Video structure
1. **Hook:** "I gave AI five tasks from my job. Here's my honest score." Show the final scorecard blurred.
2. **Ground rules:** synthetic data, I mark it, same prompts.
3. **Tasks 1–5:** one chapter each: the task in 10 seconds, Claude working (sped up), the result, my marking with REQ X-RAY-style highlights, the score.
4. **Scorecard:** all five scores, the average, time saved.
5. **Verdict:** answer the title honestly, and what it means for engineers ("match the autonomy to the risk" callback).
6. **CTA:** "What task should I test next? Comment below."

## Shorts (one per task)
"AI reviewed my requirements: 6/10", "AI ran a trade study…", and so on, each ending "Full test on the channel."

## To prepare
- [ ] Write the 15 requirements (6 flawed) and the answer key **before** running anything
- [ ] Write the 3 GPS module datasheets and the trade-study criteria
- [ ] Write the system description and the power-supply description
- [ ] Record each run in one go (screen recording per task)
- [ ] Mark each output against the answer key, on camera
