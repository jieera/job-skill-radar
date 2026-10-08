# Methodology

## Scope and counting

Markets are derived from job locations, never company nationality. A multi-market job can count in both US and China charts, but counts once in the combined set. Internships and new graduate roles are selected by explicit titles or campus-project labels. A degree requirement alone does not establish seniority. Unknown-level jobs require opt-in.

Categories are multi-label keyword rules on the title and description. Category membership is a navigation aid, not a learned classifier. ECE covers embedded / firmware, robotics software, CUDA and systems software. Pure hardware roles are included only if the description also matches a software direction.

Coverage = unique active matching job IDs with the selected skill and evidence level / all active matching job IDs. Filtering an evidence level changes the numerator, not the denominator. Selecting a skill narrows the actual role set. The comparison chart ignores only the market filter and calculates separate country denominators. There is no statistical extrapolation to the whole market.

## Extraction

HTML is normalized to text while preserving paragraph/list boundaries. Scripts and styles are ignored. Canonical skills and aliases are in `config/skills.json`. ASCII word boundaries avoid confusing Git with GitHub or Java with JavaScript, and allow Chinese text beside English names.

Evidence comes exclusively from the body. Section headings set a default requirement level; sentence cues override it, with explicit preferred and negation handling. Sentences that cannot be classified remain uncertain. A phrase “no Python required” is a mention, not a mandatory skill. Alternatives and conjunctions are preserved in the original sentence; the system does not resolve logical qualification alternatives.

Known limitations: skills not in the dictionary, abbreviations with multiple meanings, mixed preferred/required clauses in one sentence, nested qualification sections, and cultural differences in recruitment wording. Every inferred level is inspectable through original evidence.

## Updates and source health

A stable source ID identifies each job. The description hash detects updates; original first-seen time survives edits and reopening. One missing complete scan does not hide a job. Two complete successful scans mark it inactive. Incomplete pagination is never considered a complete scan.

A failed scan preserves previous jobs. A partial scan can refresh fully parsed individual jobs, but never expires unobserved jobs. Source `last_success` advances only after a complete scan; `checked_at` records every attempt. Pending sources contribute no data. Targeted runs preserve other source records.

Full descriptions may be written to an explicitly requested local `.cache` review file. The public snapshot stores evidence, not page HTML. The optional `RADAR_HTTP_CACHE` transport cache is for local debugging only (one-hour TTL); scheduled production runs do not enable it.

## Evaluation

Skill-set precision and recall are micro-averaged across reviewed records: TP/(TP+FP), TP/(TP+FN). Requirement-level accuracy is evaluated separately when labels provide evidence levels. Unreviewed records are excluded, never treated as empty labels. Agent and human review results must be reported separately.

The project includes 40 review samples and an evaluator. The human acceptance target is at least 90% precision on at least 40 independently reviewed real descriptions spanning both languages and all four categories. A curated excerpt benchmark alone cannot establish full-description extraction performance. Until that review is complete, production accuracy is unverified.
