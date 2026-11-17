---
name: writing-guide
description: Build and refine an author's writing guide from matched samples, substantive briefs, blinded comparisons, and accepted edits. Use for personal voice calibration or drafting with an existing author guide.
metadata:
  version: "1.0.0"
---

# Writing guide

Help the author express their own ideas in a voice supported by their writing. A guide starts as a hypothesis. Describe it as calibrated only after evaluating drafts against reserved examples.

## Choose the task

- **Draft or revise.** Use the material and author guide already available. Calibration is optional for an ordinary writing request.
- **Build or improve a guide.** Read [references/calibration.md](references/calibration.md). Establish a sample set, reserved examples, writer model, evaluator, and run budget before generating batches.
- **Learn from edits.** Apply the author's corrections to the current draft. When asked to update the guide, compare the before and after versions and retain only specific corrections supported by those edits. Keep audience-specific changes scoped to that audience.

## Draft from substance

Infer the audience, purpose, format, and desired length from the request. Build a compact internal brief with the author's thesis, supporting facts and sources, experiences, necessary quotations, uncertainties, and the reader's decision or next action. Keep exact quotes distinct from paraphrases.

If a missing opinion or experience would determine the piece, ask one focused question. When the user wants possible arguments, present them as proposals for the author to choose. Voice matching cannot establish what the author believes or has done.

For ordinary editing of the author's own prose, keep their wording and reasoning where they work. For evaluation, derive a separate brief that preserves substance while removing distinctive phrasing and rhetorical devices. Keep the reference original out of the draft generator's context.

## Match evidence to the format

Prefer recent, clearly authored pieces in the target format. Read complete passages to understand how the author develops an argument, qualifies a claim, and moves between paragraphs. Treat short replies as evidence about conversational register. Establish long-form voice from sustained prose or authored speech in context.

Use the guide and examples that match the current audience. Preserve useful repetitions, uneven rhythm, uncertainty, and personal phrasing when the evidence supports them. Do not add jokes, confessions, slang, anecdotes, or first-person achievements to manufacture a voice match.

For Arjun, use the installed `write-in-my-voice` skill when it applies, including its live-source requirements and final voice pass. Locate it in the current skill catalog or the user skill directories for Codex, Claude, and shared agents. For long-form calibration, keep format-matched samples separate from its conversational calibration. If that skill is unavailable, work from supplied samples and disclose any limit that affects the draft.

Apply the installed `unslop` skill when available. Keep factual fidelity and the author's demonstrated voice through editing. Keep specific sample facts separate from the new piece's source material.

## Check and deliver

Compare the draft with its brief. Verify claims, exact quotations, qualifications, ownership, timing, and the force of each request. Then compare whole paragraphs with the matched voice evidence. Revise departures you can name, such as an invented punchline or an overstated conclusion.

Return the requested prose. Keep source limitations outside the draft. Show experiments, intermediate versions, or scoring reports when requested. A draft remains ready for the author's review until they approve publishing or sending.

## Store learning deliberately

Keep sample originals, briefs, generated drafts, and evaluation records in the task's working directory. Keep private examples out of the shared fleet skill. A reusable author guide should contain concise observations and corrections, with evidence references and the format and model it was evaluated with.

When the user asks to retain a guide update, save a versioned candidate and its evaluation results. Promote improvements supported by the agreed evaluation. Keep a provisional label when evidence is limited, and recheck after a material change of writer model or writing format.

The method and its limits are documented in [references/source.md](references/source.md).
