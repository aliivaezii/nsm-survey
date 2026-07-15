# Codebook: `survey_responses.csv`

Thirty responses, 39 variables. One row per respondent. Empty cells and the literal string `null` both denote a question that was not answered or not shown. All free-text fields were screened for personal and company identifiers before release.

## Identifiers and metadata

| Variable | Description |
|---|---|
| `id` | Sequential respondent identifier |
| `submitted_at` | Submission timestamp (UTC) |

## Firmographics

| Variable | Description |
|---|---|
| `role` | Respondent's role (founder, product, growth, marketing, analytics, etc.) |
| `experience_years` | Professional experience bracket |
| `industry` | Industry of the respondent's firm |
| `region` | Operating region |
| `lifecycle_stage` | Firm lifecycle stage (pre-seed to mature) |
| `funding_raised` | Funding bracket |
| `employee_count` | Headcount bracket |
| `b_business_model` | Self-reported business model, free text |
| `b_growth_stage` | Self-reported growth stage |
| `bm_archetype` | Business model coded into archetypes: BM1 (SaaS/Subscription), BM2 (Marketplace/Transactional), BM3 (B2B/Enterprise). `b_business_model` and `b_growth_stage` were added after the first response was collected, so respondent 1 is structurally missing on these fields and is retained in pooled analyses only |

## Section B: metric practices

| Variable | Description |
|---|---|
| `b1_primary_metric` | Whether the firm tracks a single primary metric |
| `b2_nsm_familiarity` | Familiarity with the NSM concept |
| `b3_nsm_defined` | Whether an NSM is formally defined |
| `b4_nsm_revised` | Whether the NSM has been revised |
| `b5_okr_familiarity` | Familiarity with OKRs |
| `b6_okr_use` | Whether OKRs are used |
| `b7_experiments` | Growth experimentation frequency |
| `b8_data_driven` | Self-assessed data-driven decision culture |
| `b9_nsm_name` | The firm's actual North Star Metric, free text |

## Section C: direct criterion importance (1 to 7 scale)

`c1_value_alignment`, `c2_measurability`, `c3_actionability`, `c4_predictive_power`, `c5_team_alignment`, `c6_gaming_resistance`, `c7_experiment_sensitivity`, `c8_strategic_fit`

## Section D: Best-Worst Method comparisons

| Variable | Description |
|---|---|
| `d1_best_criterion` | Criterion judged most important |
| `d2_worst_criterion` | Criterion judged least important |
| `d3_best_to_others` | JSON object, best-to-others comparison vector (1 to 9 scale) |
| `d4_others_to_worst` | JSON object, others-to-worst comparison vector (1 to 9 scale) |

## Section E: per-metric ratings

| Variable | Description |
|---|---|
| `e_metric_ratings` | JSON object, respondent's rating of each candidate metric on each criterion; used to build the survey-derived decision matrix |
| `e1_other_metric` | Preferred metric outside the candidate set, free text |

## Section F: selection process

| Variable | Description |
|---|---|
| `f1_selection_method` | How the current primary metric was chosen |
| `f2_changed_nsm` | Whether the firm has changed its NSM |
| `f2a_change_reason` | Reason for the change, free text |
| `f3_comments` | Closing comments, free text |
