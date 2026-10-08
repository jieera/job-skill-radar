# Evaluation record

The corpus contains **40 distinct real-job excerpts**, 20 Chinese and 20 English, drawn from 40 source job IDs. Each direction has 10 examples. Source URLs and original text are retained. Labels were reviewed by the coding agent separately from the extractor's output, **not by a human**. Some source jobs use similar recruiting templates; this is a convenience sample and not a random or held-out benchmark.

The task is closed-vocabulary skill presence on these excerpts. Generic technology mentions not represented in `config/skills.json` are outside this evaluation. A canonical skill can still be labeled when wording differs from a configured alias, allowing missed synonyms to count as false negatives. Empty reference lists are intentional negative cases, not unreviewed examples.

## Observed baseline

- True positives: 65; false positives: 0; false negatives: 9.
- Micro precision: **100%**; micro recall: **87.8%** on this narrow agent-reviewed excerpt sample.
- Human-reviewed records: **0**. The 40-description human acceptance requirement is **not met**.
- Requirement-level classification accuracy is **not measured** by this corpus. It has regression tests only.

Do not use the 100% number as a claim about production accuracy. The sample is small, curated, excerpt-only, and drawn partly through category rules. The extractor was not tuned to eliminate these reported misses. The error list is retained in `results.json`.

```sh
python3 -m radar.evaluate --output docs/evaluation/results.json
```

## Independent human review

Use the original source URL to review the entire description, not only the selected excerpt. A local full-description worksheet was prepared at `.cache/human-review-full-descriptions.json`; this ignored artifact is not published because it contains full employer text. For another collection, save local review inputs with:

```sh
python3 -m radar.cli --review-output .cache/review_jobs.json
```

A reviewer should independently choose `expected_skills`, record `review_status: "human-reviewed"`, retain `language` and `category`, and evaluate a separate JSON file with `--corpus`. Do not simply relabel agent output as human-reviewed. Pending/null labels are excluded, and a genuine empty reviewed list remains a negative sample. Full-description human performance should be reported separately from this excerpt baseline.
