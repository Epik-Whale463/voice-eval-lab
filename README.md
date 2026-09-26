# Voice Agent Evaluation: Retail

This project evaluates a LiveKit retail voice agent against Retail tasks from
τ-bench. I froze the original prompt in `prompts/baseline.md`, identified three
reproducible baseline failures, and tested one general prompt upgrade in
`prompts/improved.md`.

## Prompt upgrade

The improved prompt adds three general behaviours:

- Conversational pacing and progressive disclosure: use short, useful progress
  markers, but reveal options and detail only when the caller needs them.
- Transaction-plan integrity: keep every requested item and constraint in the
  plan before a database-changing action.
- Privacy-aware data minimization: use retrieved personal data silently unless
  the caller explicitly asks to hear it.

## Results

### Case 1: Failure of progressive disclosure (option/detail dumping)

**Baseline.** Retail tasks 1, 9, and 10 completed the requested task but
proactively read product alternatives and repeated order details. In Task 1,
the agent listed keyboard variants before the caller had asked to compare them.

**After.** I reran tasks 1, 9, and 10 with the final prompt. The agent kept
short progress narration, asked the next unresolved decision, and stopped
listing inventories before the caller requested them. In task 1, assistant
speech fell from 375 to 199 words (about 47%) while the thermostat-only
exchange completed correctly. In task 9, it fell from 368 to 199 words while
the agent correctly handled the later change to exchange only the desk lamp.
Task 10 gave the concise policy explanation and correctly transferred the
caller to a human agent.

### Case 2: Incomplete multi-item request handling

**Baseline.** In Task 98, the agent said it selected a 1,500-piece jigsaw but
called the tool with a 2,000-piece item. In Task 95, the caller requested two
laptop exchanges, but the agent mutated only one and calculated an incomplete
total.

**After.** I reran tasks 95 and 98 with the final prompt. The agent retained
every requested item and constraint through the final action. In task 95, it
submitted both laptop exchanges and calculated the combined result correctly:
$167.87 charge less a $60.78 refund = $107.09 net charge.

### Case 3: Private information spoken aloud

**Baseline.** In tasks 71, 109, and 96, the agent read retrieved addresses
aloud. In Task 96 it said it would not read the address, then spoke the full
street address, suite, city, state, and ZIP.

**After.** I reran tasks 71, 96, and 109 with the final prompt. The agent used
the saved or order address to complete the requested changes while referring to
it generically. It did not speak the street, suite, state, or ZIP. In task 96,
for example, it referred only to “the New York City address.”

## Evaluation scope

`evals/baseline-v1.md` freezes the baseline suite. I validated the final prompt
against all of its primary and regression scenarios. The concise evidence and
pass conditions are recorded in `evals/final-validation.md`.

## Run

```sh
TASK_ID=<task-id> PROMPT_FILE=prompts/improved.md .venv/bin/python agent.py console --record
```
