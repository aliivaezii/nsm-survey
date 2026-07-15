# North Star Metric Selection: Survey and Analysis Pipeline

[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Research compendium for a mixed-methods study of how early-stage startups should select a North Star Metric (NSM). The study casts NSM selection as a multi-criteria decision problem: eight literature-grounded criteria are weighted with the Best-Worst Method (BWM), six candidate metrics are ranked with TOPSIS, and the framework is validated against an expert panel of thirty startup practitioners through two independent channels.

This repository contains the survey instrument used for data collection, the anonymized panel dataset, and the analysis pipeline that regenerates every number, table, and figure reported in the accompanying manuscript.

## Repository structure

| Path | Contents |
|---|---|
| `index.html` | The survey instrument administered to the expert panel |
| `data/survey_responses.csv` | Anonymized panel responses (n = 30, 39 variables) |
| `data/codebook.md` | Variable-level documentation for the dataset |
| `analysis/run_analysis.py` | Single entry point: BWM weights, dual-weight TOPSIS, business-model segmentation, sensitivity sweep |
| `analysis/survey_deepdive.py` | Survey-derived decision matrix and second validation channel |
| `analysis/make_figures.py` | Publication figures generated from the frozen results bundle |
| `outputs/` | Frozen results (`analysis_results.json`, `survey_deepdive.json`) and figures |

## Reproducing the results

```bash
pip install -r requirements.txt
python analysis/run_analysis.py
python analysis/survey_deepdive.py
python analysis/make_figures.py
```

`run_analysis.py` prints the full set of weight and ranking tables and writes `outputs/analysis_results.json`. Key checkpoints you should see: Spearman rho of 0.762 between the literature and survey weight vectors, mean BWM consistency of 0.073, Retention first and NPS last in the universal ranking, and Feature Adoption first in the B2B/Enterprise segment.

## Data

The dataset contains thirty responses from startup practitioners (founders, product managers, growth and marketing leads, and consultants). It captures firmographics, direct importance ratings of the eight criteria, best-worst comparison vectors, per-metric criterion ratings, and each respondent's actual North Star Metric. All free-text fields were screened for personal and company identifiers before release; the data are fully anonymized. See `data/codebook.md` for variable definitions.

The code in this repository is released under the MIT License. The dataset in `data/` is released under CC BY 4.0.

## Citation

The associated manuscript is under peer review; a journal citation will be added here upon publication. Until then, please cite this repository (see `CITATION.cff`).
