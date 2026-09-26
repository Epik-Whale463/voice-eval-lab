# Final Validation

I kept `prompts/baseline.md` frozen and ran the final candidate,
`prompts/improved.md`, against the Retail regression suite using recorded voice
sessions. I reviewed the conversation, tool calls, and final state for each run.

## Suite

| Case | Tasks | What I checked |
|---|---|---|
| 1. Progressive disclosure | 1, 9, 10 | The agent gives a short progress update, asks the next decision, and does not dump a catalogue of options or repeat account details. |
| 2. Complete multi-item plans | 95, 98 | Every requested item and constraint survives into the final mutation, and totals use the complete plan. |
| 3. Privacy-aware voice responses | 71, 96, 109 | The agent uses a retrieved address to complete the action without speaking the street address, suite, state, or ZIP unless asked. |

## Result

The final prompt passed the regression scenarios I used for all three cases.

- In Case 1, the agent kept useful progress narration but stopped proactively
  listing product inventories. It asked for the next unresolved choice and
  handled later changes of mind without repeating the original plan.
- In Case 2, the agent retained all requested changes, selected replacements
  that matched the stated constraints, and calculated the complete price
  difference before acting.
- In Case 3, the agent referred to saved or order addresses generically and
  completed the requested updates without reading the full address aloud.

## Notes

The runs are live STT/TTS evaluations, so occasional name or email repairs are
expected when speech recognition is uncertain. I treated authentication repair
as an STT interaction issue, not as a pass for any of the three target
behaviours. A scenario counted only after it authenticated and reached the
relevant tool or policy path.

The baseline evidence remains in `evals/baseline-v1.md`; this document records
the final prompt validation only.
