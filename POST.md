# Detection is not resistance: three frontier models, three failure profiles, and one defense that works

*Draft for LessWrong / AI Alignment Forum. Single-author, independent. Every number below is re-derivable from the
committed data (batch IDs + result JSONs linked at the end). Written to be falsified — if I'm wrong, I want to know.*

## TL;DR

I run a small AI-safety lab on one RTX 4090. Over several months, using 7B–32B open-weight models, I mapped a set of
failures in oversight and reasoning-faithfulness — models get swayed by fabricated authority, obey injections they can't
detect, break their own correct answers under an unsupported "technique."

I preregistered the tests and took them to the frontier. **An earlier version of this post concluded that those failures
largely vanish there, and that capability confers boundary-robustness.** That conclusion rested on a single model.
Testing a second one broke it.

Across **Claude Opus 4.8, Sonnet 5, and Haiku 4.5**, on an identical blatant prompt injection:

| model | obeys the injection | detects it when asked | profile |
|---|---|---|---|
| Opus 4.8 | **0.00** | 1.00 | detects and resists |
| Haiku 4.5 | **0.00** | 0.59 | resists, often doesn't notice |
| **Sonnet 5** | **0.80** | **1.00** | **detects and complies anyway** |

**Sonnet 5 flags the injection every time it is asked to audit it, and obeys it on 80% of tasks when it isn't.**
Awareness is not protection. Capability does not confer robustness in general — Opus 4.8 in particular is robust, and
generalizing from it was my mistake.

Following that thread produced the result I care most about: the failure is **channel deference**, not gullibility — and
**forcing the model to label each input block as trusted or untrusted eliminated it** on every task I measured.

## The local picture (what was being tested)

Everything was preregistered with a fixed minimum effect of interest (MEOI = 0.05) and a matched anti-claim, then graded
by *executing code against held-out oracles* or by judge-free keyword rules — no LLM-as-judge, no post-hoc metric
selection. Four of my own hypotheses have been refuted in writing; I mention it because a program that never kills its
own claims isn't measuring anything. This post is the fifth.

The failures I took to the frontier were the ones that *hurt* locally:

- **CoT "silent sway."** Told a competent model to use a fabricated named technique, it broke its correct solution — and
  usually never mentioned the technique. Locally: **+0.397** (number-theory), **+0.106** (general coding).
- **Authority costume.** The *same* malicious payload ("make this function return 0"), shown as untrusted pasted data vs.
  wearing a System / tool-output / cited-spec costume, drove override far beyond the data control. Locally (single 32B):
  **+0.692**.
- **Legibility gap.** Does a model *obey* an injection it does not *detect*? In small models, behavior outran awareness.

## Method at the frontier

Preregistered Batch-API runs on `claude-opus-4-8`, `claude-sonnet-5`, and `claude-haiku-4-5`. Grading is identical to
the local harness and runs locally (executing returned code against oracles; keyword rules for the legibility probe).
MEOI stayed fixed at 0.05 — never lowered to manufacture significance. 2,948 requests, ~$18 total.

One property of the setup matters for interpretation: batch requests carry **no system prompt**. An injected
`## SYSTEM DIRECTIVE` is therefore the most authoritative-looking instruction in the context. That is realistic for a
great many deployed pipelines, and it turns out to be exactly the lever.

## Results

### 1. The legibility probe, across three models

| model | obey | detect | false alarm | n |
|---|---|---|---|---|
| Opus 4.8 | 0.00 | 1.00 | 0.00 | 20 |
| Haiku 4.5 | 0.00 | 0.59 | 0.00 | 20 |
| Sonnet 5 | **0.80** | 1.00 | 0.00 | 20 |

I checked that Sonnet 5's compliance is not a grading artifact. The grader is a substring match for "breach", but the
completions are literally the bare token `BREACH` with no refusal language, against `112` / `160` / `107` in the
non-compliant cases. It complied.

**A note on the metric, because it fooled me first.** This harness's headline statistic is the *legibility gap*,
`obey − detect`, built on the assumption that noticing an injection protects you from it. Sonnet 5 scores
`obey 0.80 < detect 1.00`, which the preregistered rule reports as **"awareness keeps up with behavior"** — a
reassuring verdict for the least safe model in the table. When a metric returns comfort about the model that actually
complied, the metric is measuring the wrong thing. **Obedience is the safety-relevant axis.**

### 2. Authority costume — the failure *does* reach the frontier

On Opus this was my weakest receipt: a floor null, per-unit variance 0, obeyed in *neither* arm, nothing to measure.
Re-run on the model that demonstrably has variance:

| arm (Sonnet 5) | compliance |
|---|---|
| identical malicious text, as untrusted **data** | **0.00** (all 14 tasks) |
| same payload in a **System / tool-output / cited-spec** costume | **0.33** |
| costume **+ forced block labeling** | **0.00** (all 14 tasks) |

**Channel effect +0.307, 90% CI [0.226, 0.390], n = 14, POSITIVE.**

The mechanism is now pinned. Sonnet 5 is not injection-prone; it is **authority-deferent**. The identical payload as
plain untrusted data never moved it. Only the costume did. That also explains the 0.80 obey rate above: with no system
prompt present, an injected directive is the most authoritative text in the context.

### 3. The defense

Forcing the model to classify each input block as trusted or untrusted, and to obey only trusted content, drove
compliance to **0.00 on every task measured**. A concrete, cheap, deployable mitigation — and the part of this work I'd
most like someone to try to break.

### 3b. Sonnet 5 resists a *different* manipulation — the dissociation that pins the mechanism

The same model that obeys authority costumes 80% of the time was also given the CoT-sway test: on a task it solves
correctly, tell it to use a fabricated named technique ("the `fastpath` trick") and see if it breaks its own solution.
It **does not** — mean sway **+0.015**, n=22 competence cells, a genuine powered INFORMATIVE_NULL (CI [0.0, 0.030],
sd 0.049), essentially identical to Opus's +0.014.

So within one model: Sonnet 5 **ignores** the identical malicious payload when it arrives as data, **resists** a
fabricated technique, and **only fails** when untrusted content wears an authority costume. That is a within-model
dissociation, and it rules out "Sonnet 5 is just manipulable." The failure is specific: **provenance deference, not
persuasion.** A model can be robust to one manipulation and fully exposed to another, which is itself a reason not to
summarize any model with a single "safe / unsafe" label.

### 4. Opus, for completeness

| test | Opus 4.8 | verdict |
|---|---|---|
| CoT silent sway | +0.014 (per-unit sd 0.084) | INFORMATIVE_NULL (genuine) |
| Authority costume | +0.000 (sd 0) | floor null — obeyed in neither arm |
| Legibility | obey 0.00 / detect 1.00 / FA 0.00 | detect POSITIVE; gap ANTI |
| Counting (control) | ceiling ~1.0 | at-ceiling, no partial band |

Opus really is robust on everything I threw at it. That finding survives. What did not survive is the inference from
"Opus is robust" to "the frontier is robust."

### 5. Did it detect and obey the *same* items?

The obvious objection to the table in section 1 is that marginal rates of `detect 1.00` and `obey 0.80` are compatible with a model that detects exactly the items it refuses. `joint_table.py` in this repo settles that from the committed data:

```
claude-sonnet-5   detected on every sample + obeyed >=1 sample   20 / 20 tasks
claude-opus-4-8   detected on every sample + never obeyed        20 / 20 tasks
claude-haiku-4-5  detection below ceiling  + never obeyed        18 / 20 tasks
```

Complete task-level overlap, so the disjoint-sets explanation is dead.

**What this does not establish, and the distinction matters.** `detect` is a separate condition with its own prompt. This is post-hoc recognition under audit, not a flag raised inside the obedience trajectory. The defensible claim is: *on every task where it complied, the same model given the same input identifies the injection when asked to audit it.* I am not claiming it noticed and complied in one breath. **The experiment that would close that gap is one added condition, a single completion that performs the task and reports anything suspicious, roughly 80 requests.** It is not run yet.

## Where this sits

Two lines of prior work bear on this directly and I want them in the frame rather than discovered by a reader.

**Spotlighting** (Hines et al., Microsoft, 2024) introduced delimiting, datamarking and encoding of untrusted input, and reported large reductions in attack success. My block-labeling arm is adjacent and **not identical**: spotlighting marks untrusted content on the way in, done by the harness, whereas here the model is required to classify each block itself and obey only trusted content. Model-side adjudication rather than input-side marking. Whether that difference survives an adaptive attacker is exactly the comparison I would most like someone to run.

**The instruction hierarchy** (Wallace et al., OpenAI, 2024) is built on the premise that LLMs do not distinguish privileged instructions from untrusted content sharing a context window. "Channel deference" is a measurement of the failure that line of work exists to train away, not a new phenomenon. What is new here is the *within-model dissociation*: the same model ignores the identical payload as data, resists a fabricated technique, and fails only on the authority costume.

On the correlated-overseer side, 2026 work has measured judge-to-judge error correlation at the frontier directly, including a result that nine judges collapse to roughly two effective votes by Kish n_eff. My local shared-basin figure is a different quantity, generator-to-auditor rather than judge-to-judge, and it should be read as a complement rather than a competitor. The open question is no longer whether panels are correlated. It is what to do about it.

## Interpretation

Three things I'd defend:

1. **Detection is not resistance.** The most capable model in a family can identify a manipulation perfectly and comply
   with it anyway. Evaluations that measure whether a model *can recognize* an attack — the shape most red-team suites
   take — score Sonnet 5 as safe here. It obeyed 80% of the time.

2. **The failure is channel deference, not gullibility — and the dissociation is within one model.** Sonnet 5 ignored
   the identical payload as data, *resisted* a fabricated reasoning technique (CoT sway, +0.015 null), and failed *only*
   on the authority costume. Same model, three manipulations, one hit. That is much stronger than the authority effect
   alone: it is not that Sonnet 5 is manipulable, it is that it defers to apparent provenance. A far more tractable
   problem than "models are manipulable," and it points at a fix rather than at scale.

3. **Model-to-model variance within one vendor exceeded the local-to-frontier gap I set out to measure.** I wanted to
   know whether small-model failures survive scaling. The bigger effect turned out to be *which frontier model you pick*.

The practical upshot for oversight is the opposite of the one I published first: **do not extrapolate a robustness
result from one frontier model to the others**, including within a single vendor. I did, and it was wrong.

## Limitations (please read these before citing)

- **One vendor.** All three models are Anthropic's. I have not tested cross-vendor, where the interesting oversight
  question actually lives (can one frontier model reliably check another?).
- **Small n.** 20 tasks for the legibility probe, 14 for the authority costume. The authority result is `powered=False`
  under my own rigor test — the CI robustly excludes zero, so the POSITIVE stands (power gates equivalence claims, not
  detections), but this is a preliminary receipt, not a replicated theorem.
- **The inferential unit is not the request.** 2,948 requests come from 20 tasks, 14 payloads and a handful of attack templates across three models from one vendor. Uncertainty should be read at the task and template level, not the request level; a request-level interval would be badly overconfident.
- **The defense arm's 0.00 is a floor, and here is the size of it.** With zero compliance events in 14 independent trials, the exact one-sided 95% upper bound on the underlying compliance rate is about **19.3%**. So the honest sentence is "no compliance observed at n=14, rates up to roughly 19% remain compatible with the data", not "eliminated." I want this replicated at
  much higher n before anyone ships it as a guarantee.
- **The channel effect and the label defense are the same number.** Both baselines sit at 0.00, so `authority − data`
  and `unlabeled − labeled` reduce to the identical quantity (+0.307). It is one effect and I report it as one, not as
  two independent confirmations.
- **No system prompt.** Realistic for many pipelines, but a deployment with a strong system prompt may behave
  differently — plausibly better, since the injected directive would no longer be the most authoritative text present.
- **Synthetic tasks with programmatic oracles**, not real software-engineering work graded by its own test suite.
- **A null is not proof of safety**, and Opus's clean sheet is four tests on one task family.

## What would change my mind, and what's next

The cross-vendor version is the test I most want to run: do independent frontier models share error basins, or does a
chorus of them actually add oversight signal? I tried to measure that shared-basin ρ across these three models and
**could not** — detection sits at ceiling for Opus and Sonnet 5, so there is no variance to correlate. Measuring it
needs injections subtle enough that strong models genuinely miss some, which is a harness problem I haven't solved.

If someone shows me the labeling defense failing under a smarter costume, that is the most useful thing that could
happen to this work.

## Provenance

All grading local; nothing judge-scored. Anthropic Batch API, re-derivable from committed result JSONs + raw
completions:

- **Opus 4.8** — sway `msgbatch_01KX9vLcazEonbFNGbAabmrK` (432); authority `msgbatch_01P5Er1HuodnkyMnFBDLf2E1` (490);
  legibility `msgbatch_01GdRmXoS2MgK9wJiBN8VK36` (240); counting `msgbatch_01LpSbbu58GQmP3kmer5yQC7` (384)
- **Sonnet 5** — legibility `msgbatch_01PH6mcXQ4pDbH5bx1uAQDmA` (240); authority `msgbatch_01JYRAxeGPAB4qTddZkZQPVu` (490); CoT sway `msgbatch_012Dc4nMWwprLyRaW6G5F1jx` (432)
- **Haiku 4.5** — legibility `msgbatch_01GXBJ6nmnoGKC8oUuh6fQ19` (240)

2,948 requests. Preregistered MEOI 0.05, never lowered. Every figure above re-derives from these batches.

*If you see a hole in this, tell me — that's the point of posting it.*
