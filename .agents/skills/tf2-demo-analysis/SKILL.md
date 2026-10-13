---
name: tf2-demo-analysis
description: Analyze Team Fortress 2 demo summaries with reproducible, privacy-preserving individual metrics and Markdown reports. Use for post-match `.dem` analysis in this project; not for live coaching or video analysis.
---

# TF2 demo analysis

Use this skill for an individual post-match report from a local TF2 demo. Keep calculations deterministic: use the project's scripts and parser output; never estimate metrics in prose or with a language model.

## Workflow

1. Read the project's `AGENTS.md` and `docs/VALIDACAO_DEMO.md`. Check `git status` before changes and preserve existing work.
2. Use the user-specified `.dem` or an already parsed JSON. Do not scan unrelated personal directories. For a demo, record its byte size and SHA-256; preserve the original and keep demo, parsed JSON, and report under ignored `data/` paths.
3. Reuse valid JSON when available. If parsing is needed, use `tf-demo-parser` **0.7.1** or another version explicitly documented by the project. Check the documented source, license, and build instructions first. Ask for approval before a required download or network access when the current session has not authorized it. Do not add the parser as a project dependency.
4. Validate JSON syntax and inspect only the fields needed for analysis. Do not print or copy raw chat, player names, SteamIDs, or server names into logs or reports.
5. Identify the POV by an exact match of `header.nick` to `users[].name`, resolving through the matching user's ID/SteamID internally. If it is ambiguous or absent, ask for the target player's SteamID. For a player other than the POV, require an explicit SteamID. Never include the SteamID in the report.
6. Run the deterministic analyzer:

   ```bash
   python3 scripts/analyze_demo.py data/parsed/<summary>.json
   ```

   Use `--steam-id <id>` only when needed to select the requested player; the script does not write that value to the report. Reports default to `data/reports/` and must remain private. The script refuses to overwrite an existing report unless `--force` is passed, and never allows the output path to replace the source JSON; prefer a new `--output` path when preserving prior reports.

7. Review the Markdown against the source fields. `deaths[].killer`, `victim`, and `assister` support player-specific event counts; values of `deaths[].weapon` apply only to that player's attributed eliminations and are parser labels, not proof of an equipped weapon. Round winners and lengths are global context, not individual stats. Tick-derived seconds require both `startTick` and `intervalPerTick` to be compatible with event ticks; otherwise report ticks only. Never infer positions, aim, visibility, class-change timing, or continuous activity from the summary.
8. Run `python3 -m unittest discover -s tests -v`. Report the metrics' source fields and any missing data or schema limits.

## Privacy and maintenance

- Ignore `chat` entirely in reports. Omit player names, SteamIDs, server names, and third-party identifiers.
- Keep demo, parser JSON, and reports in Git-ignored `data/`; do not upload or commit them.
- When parser output changes, document the observed schema in `docs/VALIDACAO_DEMO.md`, update the anonymized fixture/tests, then run the full suite. Keep parsing in the parser and derived metrics in application code; this skill describes the procedure only.

Invoke explicitly with `$tf2-demo-analysis` when automatic skill selection does not activate it.
