# 11 Learn: turn feedback and results into rules (monthly, and before a new stage)

**When:** once a month in stage 5 (gate G5 asks for it every five weeks), and whenever a stage or a large change ends.
**Inputs:** `bin/asf feedback patterns`, `bin/asf feedback list --all`, `docs/lessons.md`, the results of finished changes (`bin/asf change list --all`, each brief's "What it should move" and its recorded result).
**Output:** proposed rules for a person to accept or reject. Nothing is promoted without them.

```text
Run the learning pass for [CLIENT].
1. Run `bin/asf feedback patterns` and `bin/asf feedback list --all`. Read every piece of feedback since the last pass, not only the tagged ones.
2. Find what recurs: the same point made twice, by the same person or by two people, on different pieces. Give untagged feedback a theme.
3. For each recurring point, draft one rule: a single sentence someone could check a design or a page against. Say which feedback it comes from and what it would have prevented. Skip one-offs and matters of one person's taste on one piece.
4. Read the finished changes: for each with a result, did it move what its brief said it would? Draft a rule only where the result says something we would do differently next time.
5. Read every "overruled" item: we built it as asked although the evidence said otherwise. What happened? If the concern was right, say so plainly with the result. If it was wrong, say that too, and propose removing or softening the rule it came from.
6. Check docs/lessons.md for rules that contradict each other or that a later result disproves. Propose striking them, with the reason.
7. Mark any rule that would hold on any site as "for the framework": it goes to the framework's principles or patterns, with what happened.
Show me the list: each proposed rule, its evidence, and what it changes. Promote only the ones I accept
(`bin/asf feedback promote <id> --rule "…" [--scope framework]`), then record the pass with my name:
`bin/asf feedback reviewed --by "<name>"`.
```
