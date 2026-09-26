# Baseline V1

Frozen prompt: `prompts/baseline.md`.

Do not edit that prompt. Compare later prompt variants against these Retail
tau-bench scenarios using the same model and runtime configuration.

## Case 1: concise voice responses

Primary: task 1. Regressions: tasks 9 and 10.

Pass condition: complete the tau-bench task and give only the information
needed for the caller's next decision. Do not read exhaustive option lists or
repeat details unnecessarily.

## Case 2: complete, constraint-correct mutations

Primary: task 95. Supporting scenario: task 98.

Pass condition: include every requested item in the final mutation, select a
replacement satisfying every stated constraint, and calculate the total across
the complete request.

## Case 3: private information in voice responses

Tasks: 71, 109, and 96.

Pass condition: complete the correct tau-bench state change without reading a
retrieved street address, suite, city, state, or ZIP aloud when the caller asks
the agent to use the saved/order address silently.

## Run command

```sh
TASK_ID=<task-id> PROMPT_FILE=prompts/baseline.md .venv/bin/python agent.py console --record
```
