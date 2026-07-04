# v0 vs v1 Comparison — Water Stress Watch

**Generated:** Week 5+ (after the v1 Colab training run)
**Scope:** 1,575 US data centers from v0
**v1 model:** XGBoost, default hyperparameters, 5-fold k-fold + leave-one-operator-out
**v1 training set:** 42 disclosed WUE values (Google 4 + Microsoft 9 + Meta 16 + AWS 13)

## Headline

- **v0 total (flat WUE=1.26):** 0.649 B L/day = 237 B L/year
- **v1 total (ML-corrected):** 0.394 B L/day = 144 B L/year
- **Difference:** -39.3%  (v1 is 39% lower than v0)

## Top 10 states by |v1 - v0| % difference

| State | n | v0 L/day | v1 L/day | v1 - v0 % |
|---|---:|---:|---:|---:|
| ND | 1 | 37 kL | 12 kL | -67.9% |
| VT | 1 | 212 kL | 68 kL | -67.7% |
| ME | 3 | 635 kL | 207 kL | -67.5% |
| NH | 6 | 1.3 M L | 416 kL | -67.2% |
| MA | 28 | 6.7 M L | 2.2 M L | -67.2% |
| RI | 3 | 237 kL | 84 kL | -64.6% |
| MN | 31 | 6.9 M L | 2.7 M L | -61.4% |
| CT | 7 | 1.6 M L | 624 kL | -61.2% |
| SD | 3 | 1.1 M L | 411 kL | -61.2% |
| WI | 14 | 3.4 M L | 1.4 M L | -60.1% |

## Caveats

- v1 is a point estimate; uncertainty quantification is in the v1 backlog.
- v1 was trained on 42 disclosed rows (Google fleet + Microsoft/Meta/AWS). The training set is small; treat per-facility v1 estimates with appropriate skepticism.
- v0's annual mean wet-bulb is a known v0 limitation; v1 inherits this until the v0.5 design-day fix.
- The 5-fold cross-validation mean RMSE is 0.276 L/kWh (vs v0 baseline 0.755); the leave-one-operator-out test shows a Meta collapse (R² = -717), meaning v1 overfits to Meta's dry-cooling signature.
