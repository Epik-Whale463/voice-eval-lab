# Retail Voice Agent Evaluation

## Implementation approach

I built a small LiveKit voice agent for the official tau-bench Retail domain.
The agent uses Deepgram for STT and TTS, a configurable LLM, and the original
tau-bench Retail environment for policies, task state, and tool execution. I
did not recreate the retail tools or database logic.

Each run records the LiveKit conversation events, tool calls, prompt hash,
customer scenario, and final environment state. This makes it possible to
inspect the spoken interaction as well as verify the underlying transaction.

I established a frozen baseline, then evaluated a single general prompt update
against three behaviours:

- option and detail dumping before the customer needs it;
- losing part of a multi-item request before taking an action; and
- reading retrieved address details aloud unnecessarily.

The prompt update adds progressive disclosure, transaction-plan integrity, and
privacy-aware data minimization. I reran the baseline scenarios with the same
tasks after the prompt change. The detailed scenarios, pass conditions, and
results are in `evals/`.

## Approaches considered and tradeoffs

I considered changing the tool layer to hide or pre-format raw catalog data.
That could reduce verbose responses, but it would make the evaluation less
faithful to the official environment and could hide a model behaviour problem.
I kept the official tool responses intact and addressed the conversational
behaviour in the prompt instead.

I also avoided task-specific instructions. The goal was one behaviour-level
prompt change that could improve unseen Retail tasks, rather than a collection
of fixes for individual task IDs.

Run recordings and traces are intentionally ignored by Git because they can
contain benchmark customer data. The repository keeps the reproducible code,
prompts, test cases, and concise evaluation notes; recordings can be shown in
the demo.

## Future improvements

- Add an automated transcript scorer for turn length, repeated information,
  sensitive-data leakage, and task completion.
- Run the frozen suite across more tasks, models, voices, and noisy STT
  conditions to measure whether the prompt generalizes.
- Add a presentation layer between tools and the model that returns only the
  minimum fields needed for the current decision, then compare it fairly with
  the prompt-only approach.
- Expand the regression suite to include interruptions, corrections, and
  longer multi-step customer requests.
