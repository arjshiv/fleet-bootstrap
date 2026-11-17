# Calibrate an author guide

Use this workflow when the user asks to learn, evaluate, or improve a writing voice. Start with the samples and tools available. Ask for the target format, writer model, or spending and run limits when those choices are missing and consequential.

## Prepare evidence

Choose a focused set of recent authored pieces in one format. Roughly a dozen substantial pieces can support an initial pilot. Record provenance, date, intended audience, format, and whether the author approved or published each piece. Exclude quoted third-party prose and material whose authorship is uncertain. If using transcripts, identify the author's own speech and preserve its context.

Separate related pieces and revisions as one family so they stay in the same split. Freeze development and final-test IDs before optimization. Use development cases for feedback and reserve a final set for acceptance. Include recent work in that final set when the author's style is changing. If there are too few independent pieces for a split, call the result provisional.

Record an experiment manifest with these fields.

```text
author and target format
corpus IDs and provenance
development IDs and final-test IDs
writer model and version, available generation settings, tools
judge model and version
baseline and candidate guide versions
maximum cases, rounds, calls, cost or subscription run allowance
predeclared acceptance rule and factual-fidelity requirements
```

The shared skill is the procedure. Keep an author's corpus and evolving guide in the workspace selected for that author. Ordinary drafting and feedback do not authorize edits to agent memory files.

## Make briefs without leaking the reference

Have a preparation step read each reference and produce a substance brief. The draft generator receives that brief and the guide being tested. Its context must exclude the reference original and earlier drafts of that same case.

Use this preparation prompt as a starting point.

```text
Prepare a factual brief that another writer can use independently.
Identify the thesis, intended reader, argument dependencies, facts with their
sources, the author's documented experiences, exact necessary quotations,
uncertainties, and desired reader action. Preserve every substantive constraint.
Use neutral language for paraphrases and an outline organized by dependencies.
Separate exact quotations from paraphrases. Remove the reference's distinctive
opening, punchlines, catchphrases, and sentence patterns from paraphrases.
Flag missing or contradictory evidence. Supply no replacement anecdotes.
```

Inspect the brief for accidental copying and lost meaning before using it. Some exact facts and necessary quotes legitimately overlap with the original. Keep those overlaps identifiable.

## Define a useful baseline

Compare one candidate guide with a fixed baseline using the same briefs, writer model, available settings, context, and output constraints. An existing guide is a useful baseline. A separate comparison with no guide can show whether either guide helps.

Keep generation instructions stable. Use independent contexts so the second draft cannot borrow from the first. Retain the output and actual settings for each run. If a platform exposes neither a seed nor a fixed model version, record that limitation. Repeat close comparisons within the run budget before drawing a strong conclusion.

Begin with a short candidate guide containing evidence-backed tendencies and named failure corrections. For example, if drafts keep converting tentative observations into certainty, instruct the writer to preserve the original degree of uncertainty. Keep the correction tied to the observed failure and communicative setting.

## Judge without revealing the candidate

For each development case, give the judge the reference, its brief, and anonymous drafts A and B. Keep guide names, variant labels, generation rationale, and the optimizer's preferred answer outside the judging context. Repeat the judgment in a fresh context with A and B swapped. Preserve both answers.

Use this judge prompt as a starting point.

```text
Compare two drafts with the author's reference for this format and audience.
First check each draft against the factual brief. Mark unsupported experiences,
claims, quotations, changed obligations, and lost qualifications. Then assess
how each draft develops the thought, carries uncertainty, sounds to its reader,
and moves through sentences and paragraphs. Distinguish imitation of the
reference's content from resemblance in the author's writing habits.

Choose A, B, or tie for closer voice resemblance. Give a short explanation
grounded in observed differences from the reference. Avoid rewarding polished
grammar, generic brevity, extra wit, or greater length as proxies for voice.
Return JSON with winner, faithful_a, faithful_b, and notes. The faithfulness
fields are booleans and account for the entire factual brief.
```

A writer's own review remains necessary. Measure whether the judge makes the same choice after order reversal before using its feedback to drive optimization. Treat disagreement as unresolved evidence. Track factual regressions separately from style judgments.

## Score the comparison

Keep one JSONL record per case, candidate/baseline pair, writer, judge, and split. `forward` presents the candidate as A. `reverse` presents the candidate as B. These mappings belong in the evaluation record, outside the judge prompt.

```json
{"case_id":"essay-01","candidate_version":"v2","baseline_version":"v1","writer_model":"record-actual-model","judge_model":"record-actual-model","split":"dev","forward":{"winner":"A","faithful_a":true,"faithful_b":true,"notes":"Specific reference-based observation."},"reverse":{"winner":"B","faithful_a":true,"faithful_b":true,"notes":"Independent observation after swapping."}}
```

Run the bundled scorer against real completed judgments.

```sh
python3 <skill-directory>/scripts/score_pairs.py judgments.jsonl
```

The scorer normalizes the swapped labels. It reports stable candidate wins, stable baseline wins, stable ties, order-sensitive cases, and faithfulness failures. The win rate uses stable decisive comparisons as its denominator. The report also includes wins divided by all cases so unresolved cases remain visible. It rejects duplicate or malformed records and keeps models, variants, and splits separate.

Synthetic records can verify the scorer's arithmetic. They provide no evidence about an author's voice or a guide's quality.

## Improve and accept

Read the development judgments and the author's corrections. Identify one recurring failure and edit the corresponding instruction. Keep the previous guide and all experiment records. Regenerate and evaluate under the same conditions. Keep a change only when it passes the acceptance rule declared in the manifest and introduces no disallowed factual regression.

Scale the run to the available evidence. A small pilot can identify failures without proving a general advantage. Stop when the agreed allowance ends or improvements stop replicating. GEPA or another optimizer is optional when the user has authorized a larger experiment. The procedure also works as a small manual loop.

Evaluate the selected candidate once on the reserved final cases. If the final result causes another guide change, those cases have become development data. Reserve fresh cases for a later final test. Report sample counts, ties, disagreements, faithfulness failures, actual models, and scope with any claim of improvement.

Keep guide versions scoped to the author, format, and writer model. After a model change, compare the current guide with the new model's no-guide baseline before transferring an earlier performance claim.

## Learn from real edits

When the user asks to retain their corrections, compare the model draft with the author's accepted version. Separate factual corrections, changed intent, audience choices, and style edits. Turn repeated style failures into a small candidate change and cite the relevant case IDs. Retest that change before promoting an optimized version. Preserve deliberate stylistic changes even when older examples favored a different habit.
