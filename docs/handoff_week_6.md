# Handoff: Water Stress Watch — Week 6 (Post-v1.0 Decision Point)

> **Purpose:** Self-contained prompt for a fresh Hermes session to continue the Water Stress Watch project. **v0 shipped (Weeks 1-3); v1.0 trained and shipped (Weeks 4-5).** Week 6 is the next decision point — Hiroaki picks which post-v1.0 work to do, OR the session does whatever the next session is asked.
>
> Read this file once, then act.

---

## TL;DR — What to do this week

Week 5 produced v1.0: a working XGBoost model that beats v0 by 63% on RMSE in the 5-fold test (0.276 vs 0.755), predicts 144 B L/year US data center water use (vs v0's 237 B L/year), and ships as a release. **v1.0 is shippable.** But the v1.0 run exposed five real issues, all flagged in the Week 5 summary:

1. **Meta LOO collapse (R² = −717).** v1 doesn't generalize to unseen operators.
2. **Feature importance is 85% on the `cooling_type` binary.** Effectively a 1.5-feature model.
3. **State-level shift is uniform (−60% to −68%).** Not climate-driven.
4. **No uncertainty bands** on the v1 WUE prediction.
5. **−39% reduction bigger than expected.** Investigate the gap.

**Week 6 is Hiroaki's call on which to do next.** There are four concrete options below (Task 6.1-6.4). If Hiroaki doesn't pick, the session asks.

**The single most important thing for the next session: read the project state off disk first.** Don't assume Week 5 pushed anything new; check.

---

## Project Path & Owner

- **Path:** `/root/project/datacenter_water_stress/`
- **Owner:** Hiroaki Oshima (founder building AI startup in Japan, ex-CV data engineer, Berkeley DS, has Colab Pro A100)
- **Repository:** https://github.com/Hiroaki0422/datacenter-water-stress-project (public, MIT code + CC-BY 4.0 data/docs)
- **Git auth:** SSH key at `~/.ssh/github_ed25519` (no passphrase), `~/.ssh/config` is pinned to `github.com` so `git push` works without env-var overrides.
- **License:** MIT (code), CC-BY 4.0 (data, docs, methodology), WRI Aqueduct CC-BY 4.0 (water stress sub-component)

---

## READ THESE BEFORE YOU START

In this order:

1. **`docs/handoff_new_session.md`** — the project status snapshot. The "What Week 5 Built" section is the most current description of what shipped.
2. **`docs/week_5_summary.md`** — what got built in Week 5 (v1.0 trained, run summary cell added, comparison report generated). Skim the headline + caveats.
3. **`docs/v1_vs_v0_comparison.md`** — the journalism-derivative state-level rollup. The actual v1.0 numbers.
4. **`methodology.md` Section 16.9-16.10** — citable v1.0 results + journalism caveats. Read 16.10 before any public-facing communication.
5. **`notebooks/04_ml_training.ipynb` Cell 16.5 + 17** — the auto-generated run summary and the markdown version. The auto-summary re-runs on every training run.

> **Do NOT re-read the v0 docs (v0_plan.md, week_2_summary.md, data_dictionary.md) unless you need to.** They're historical context. If you do, use the `search_files` tool, not `read_file` end-to-end.

> **Do NOT re-read handoff_week_2.md, handoff_week_4.md, or handoff_week_5.md.** They're historical and stale. The current state is in this doc + the snapshot.

---

## WHAT'S ALREADY DONE (cumulative, end of Week 5)

Read these to get full context (don't re-run the pipelines):

1. `docs/v0_plan.md` — the original v0 plan, including the v1 preview section (lines 179-195)
2. `docs/week_2_summary.md` — what got built in Week 2 (estimation pipeline, 3 methodology issues found)
3. `docs/data_dictionary.md` — column definitions for all 6 v0 datasets
4. `case_studies/phoenix_az.md` — Phoenix case study (good example of how Hiroaki wants narrative content)
5. `methodology.md` — citable methodology writeup (16 sections, 7 citations, license; Section 16 is the v1 addendum; 16.9-16.10 are the v1.0 results)
6. `README.md` — public intro (links the GitHub repo, the v0 map, the Colab workflow)
7. `docs/week_4_summary.md` — Week 4 session report (v1 ML training foundation)
8. `docs/week_5_summary.md` — Week 5 session report (v1.0 trained + comparison shipped)
9. `docs/v1_vs_v0_comparison.md` — Week 5 deliverable (state-level rollup)

**Shipped artifacts on disk (all idempotent, all pushed to GitHub):**

| File | What |
|---|---|
| `data/processed/us_dc_with_stress.csv` | v0 inference table: 1,575 rows × 25 cols |
| `data/processed/ml_training_set.csv` | v1 training set: 43 rows × 14 cols (42 disclosed WUE + 1 NaN held-out) |
| `data/processed/v1_inference_features.csv` | v1 inference features: 1,575 rows × 42 cols |
| `data/processed/v1_predicted_wue.csv` | **v1.0 per-facility predictions: 1,575 rows × 17 cols** (in git) |
| `models/water_estimator_v1.pkl` | **v1.0 XGBoost model artifact: 615 KB** (NOT in git, regenerable from notebook) |
| `assets/map_v0.html` | v0 public map: 8.4 MB Folium |
| All v0 scripts in `src/clean_locations.py` through `src/build_map.py` | idempotent, no need to re-run |
| `src/build_ml_training_set.py`, `src/build_v1_features.py`, `src/v1_output_schema.py` | Week 4 v1 training foundation |
| `notebooks/04_ml_training.ipynb` | 19 cells: 1-13 train + predict, 14 save, 15 comparison plot, 16 schema, 16.5 auto-summary, 17 markdown summary, 18 schema doc |
| `notebooks/05_v1_vs_v0_compare.py` | Post-training comparison; handles missing v1_liters_per_day |
| `LICENSE` (MIT), `LICENSE-data` (CC-BY 4.0), `.gitignore` | legal + ignore |

---

## LOCKED DECISIONS (do not revisit without asking)

From Week 1 + Week 2 + Week 3 + Week 4 + Week 5 reviews (**16 questions, all locked**):

1. **MW estimation:** operator-class heuristic (already shipped in v0)
2. **Phoenix case study:** primary; Loudoun VA is backup (Phoenix case study shipped)
3. **License:** MIT (code), CC-BY 4.0 (data/docs), WRI Aqueduct CC-BY 4.0
4. **Stress granularity:** state-level for v0; sub-state is v1+ (NOT a Week 6 task)
5. **Source data:** only `orimadros_datacenters.csv` for v0 (1,605-row MIT)
6. **Week 4 scope:** v1 ML kickoff — skeleton + data collection only. Actual training is interactive in Colab UI by Hiroaki with A100.
7. **Colab Pro subscription** — notebook must be Colab-ready.
8. **v0.5 vs v1.0 naming:** v0.5 = bug fixes / methodology corrections; v1.0 = new model; v1.5 = sub-basin overlay; v2.0 = global.
9. **Lumen / Cogent reclassification:** wait for the v1 model. Revisit in v0.5 if v1 outputs look wrong.
10. **ML training target:** predict **WUE (L/kWh)**. At inference: `v1_water_lpd = v0_est_mw × 1000 × 24 × 0.7 × v1_predicted_wue × climate_adj`.
11. **Training set operators:** Google + Microsoft + Meta + AWS (region-level). Apple skipped.
12. **Validation strategy:** stratified 5-fold k-fold across all 4 operators + leave-one-operator-out generalization test.
13. **v1.0 ships at 144 B L/year** as the ML-corrected estimate; v0's 237 B L/year stays as the conservative upper bound.
14. **Both numbers should be reported** with the cooling-penalty double-counting caveat (methodology Section 9, 16.1).
15. **The −39% shift is mostly the v0 cooling-penalty double-counting** being corrected, not a real-world reduction in water use.
16. **The Meta LOO collapse is a known limitation** that v1.5 (cooling-type classifier) fixes.

(Full reasoning in `docs/handoff_week_4.md` and `docs/week_5_summary.md`.)

---

## THIS WEEK'S TASKS (Hiroaki picks one, OR do nothing)

The next session does **one** of these (Hiroaki's call). The order is **highest impact first**:

### Task 6.1 (RECOMMENDED): v1.5 cooling-type classifier

**Why:** Fixes the Meta LOO collapse (R² = −717). v1.0 is currently a 1.5-feature model where 85% of feature importance is the binary `cooling_type` flag. A real cooling-type classifier would let the v1 model use cooling type as a real feature (not a constant "unknown") and spread the feature importance.

**What it is:**

A separate classifier model that predicts cooling type (air / evaporative / water / immersion) from facility attributes that ARE in the v0 data: `latitude`, `longitude`, `wet_bulb_c`, `sqft_total_space` (47% coverage), `sqft_colocation_space` (47%), `miles_to_nearest_airport`, `operator_class`. This is a 4-class classification problem, not regression.

**Inputs:**
- `data/processed/us_dc_with_stress.csv` (1,575 rows, has lat/lon/wet_bulb/sqft/operator)
- `data/processed/ml_training_set.csv` (43 rows with `cooling_type` disclosed for Google/Microsoft/Meta/AWS)
- Plus any other public sources: Google 2024 Report has PUE+WUE per region, Meta 2024 Report has cooling tech per site

**Outputs:**
- New `src/build_cooling_classifier.py` — assembles the labeled training set + features
- New `notebooks/06_cooling_classifier.ipynb` — train the classifier (XGBoost 4-class), validate, save model + predictions
- New `data/processed/cooling_type_predicted.csv` — 1,575 rows, predicted cooling type per facility
- A new `cooling_type` column added to `data/processed/v1_inference_features.csv`
- v1.0 model retrained with `cooling_type` as a real feature → new `models/water_estimator_v1.5.pkl` + `data/processed/v1.5_predicted_wue.csv`
- Updated comparison report showing the LOO Meta improvement (expected: R² Meta goes from −717 to ~0.2)

**Acceptance criteria:**
- Cooling classifier achieves ≥ 70% accuracy on a held-out test (probably stratified by operator_class)
- v1.5 LOO Meta R² is no longer catastrophically negative (target: > 0)
- The v1.5 model's feature importance is more spread (no single feature > 50% of gain)
- The pipeline is still idempotent

**Code style:** Same as the v0 / v1 pipeline — idempotent scripts in `src/`, interactive work in `notebooks/`. The cooling classifier is a separate model artifact (not bundled with the WUE model).

**Effort estimate:** 1-2 days. Most of the work is curating the cooling-type training labels from public sources; the modeling itself is straightforward.

### Task 6.2: v0.5 design-day wet-bulb

**Why:** Localizes the climate signal. v0's `wet_bulb_c` is annual mean, which understates cooling stress (Phoenix = 12.5°C annual mean; design-day wet-bulb is ~25°C). v0's `climate_adj` is therefore ~1.0 for almost everywhere, including AZ. v1 inherits this, so the v1 model can't localize climate-driven differences between, say, Phoenix and Boston.

**What it is:**

Replace `wet_bulb_temperature_2m_mean` (annual) with the **99th-percentile daily max wet-bulb** (or 90th, or summer-only). The Open-Meteo daily cache from Week 2 (`data/external/open_meteo/batch_*.json`, 16 files) is already cached — this is a recomputation, not a network call.

**Inputs:**
- `data/external/open_meteo/batch_*.json` (16 cached API responses)
- `src/fetch_climate.py` (the Week 2 script)

**Outputs:**
- Updated `src/fetch_climate.py` that adds `wet_bulb_p99_c` (or `wet_bulb_design_c`) column
- Updated `climate_adj` formula: `1.0 + 0.03 * max(0, wet_bulb_p99_c - 15)`, possibly with a steeper slope
- Re-run `src/fetch_climate.py` → `src/estimate_water.py` → `src/join_water_stress.py` → regenerates `us_dc_with_stress.csv`
- Updated `data_dictionary.md` describing the new column
- A short addendum to `methodology.md` Section 9 (climate adjustment) explaining the change
- Updated `v1_inference_features.csv` with the new column
- v1.0 model retrained with the new `wet_bulb_c` feature → `models/water_estimator_v0.5.pkl` + new predictions
- Expected: AZ's `climate_adj` jumps from 1.0 to ~1.3-1.5, NM from 1.0 to ~1.4, northern states stay near 1.0

**Acceptance criteria:**
- Phoenix's new `climate_adj` is meaningfully different (e.g. 1.3-1.5 instead of 1.0)
- The pipeline is still idempotent
- The headline US total changes (probably 0.65 B L/day → 0.8-1.0 B L/day in v0, v1 stays near 0.4 B L/day)
- The change is documented in the methodology

**Effort estimate:** 1 day. Mostly recomputation + a methodology update.

### Task 6.3: PDF reconciliation

**Why:** The 43-row training set is honest but anchored on the well-documented public record, not the actual disclosure text. Reconciling against the actual PDFs could add 20-50 more training rows and tighten the model.

**What it is:**

Open the actual operator sustainability PDFs and tighten the WUE values. For each row in `data/processed/ml_training_set.csv`, verify the WUE value against the source. Where the report gives a more specific number (e.g. a per-region PUE+WUE not in the well-known fleet totals), use the more specific value.

**Inputs:**
- `data/processed/ml_training_set.csv` (43 rows, each with a `source_url`)
- The actual PDFs: Google 2024 Environmental Report, Microsoft 2024 Sustainability Report, Meta 2024 Sustainability Report, Amazon 2023 Sustainability Report

**Outputs:**
- Updated `data/processed/ml_training_set.csv` with refined WUE values + new rows
- Updated `src/build_ml_training_set.py` with the new values
- Comments in the script citing the exact PDF page where each value came from
- v1.0 model retrained with the new training set → `models/water_estimator_v1_reconciled.pkl` + new predictions

**Acceptance criteria:**
- At least 60 rows with verified WUE values (target: 80+)
- Each row's `notes` column cites the exact PDF page + table
- The v1_reconciled model's 5-fold R² is at least as good as v1.0 (currently 0.651)
- The LOO Meta collapse is no worse than v1.0 (currently R² = −717)

**Effort estimate:** 1-2 days, mostly PDF reading.

### Task 6.4: Lumen / Cogent reclassification

**Why:** Lumen (96 rows) and Cogent (28 rows) are fiber+colo hybrids. They're currently classified as `colocation_secondary` (10 MW default), but they could be split into separate classes with different default MWs.

**What it is:**

Update the `OPERATOR_PATTERNS` list in `src/estimate_power.py` to split Lumen and Cogent into separate classes. Cite the source (e.g. Lumen's "Enterprise" fiber + colocation split).

**Inputs:**
- `src/estimate_power.py` (the v0 heuristic)
- Lumen and Cogent's public disclosure (e.g. 10-K filings) for what fraction is fiber PoP vs colocation

**Outputs:**
- Updated `OPERATOR_PATTERNS` with new classes (e.g. `cable_telecom_lumen` with 2 MW default, `colocation_lumen` with 8 MW default)
- Re-run `src/estimate_power.py` → regenerates `us_dc_with_mw.csv` and downstream
- A short note in the methodology about the reclassification

**Acceptance criteria:**
- The reclassification is defensible (cite a source)
- The pipeline is still idempotent
- The MW total for the affected rows changes (and the headline US water total adjusts accordingly)
- Lumen/Cogent v1 predictions change in a sensible direction

**Effort estimate:** 0.5 day.

### Task 6.5 (if all 6.1-6.4 are done): Add uncertainty bands to v1.0

**Why:** v0 has ±50% bands; v1 has a point estimate. v1's journalism number (144 B L/yr) would be more credible with a range.

**What it is:**

Bootstrap the v1 model: train 100 models on bootstrapped training sets, take the 10th and 90th percentile of predictions per facility. Add `v1_liters_per_day_low` and `v1_liters_per_day_high` columns to `data/processed/v1_predicted_wue.csv`.

**Inputs:**
- `data/processed/ml_training_set.csv` (43 rows)
- `notebooks/04_ml_training.ipynb` (the trained model)

**Outputs:**
- New `notebooks/07_v1_bootstrap.ipynb` — 100 bootstrap iterations, 10th/90th percentiles
- Updated `data/processed/v1_predicted_wue.csv` with `v1_liters_per_day_low/high` columns
- A new headline: "US data center water use: 144 B L/year (95% CI: 120-170 B L/year)"

**Acceptance criteria:**
- The bootstrap range is plausible (e.g. ±25% around the point estimate, not ±5%)
- The pipeline is still idempotent
- The methodology Section 16 is updated with the new uncertainty band

**Effort estimate:** 4 hours (mostly waiting for 100 model fits).

---

## DONE-WHEN CHECKLIST

Week 6 is done when **at least one** of these is true:

- [ ] `models/water_estimator_v1.5.pkl` exists (v1.5 cooling-type classifier shipped) **AND** `data/processed/v1.5_predicted_wue.csv` is in the repo, **OR**
- [ ] `src/fetch_climate.py` has a new `wet_bulb_p99_c` column + the pipeline regenerated, **OR**
- [ ] `data/processed/ml_training_set.csv` has ≥ 60 rows with verified WUE values, **OR**
- [ ] `src/estimate_power.py` has Lumen/Cogent split into separate classes + the pipeline regenerated

The session is also done when:

- [ ] `git status` is clean (or changes are clearly intentional and documented)
- [ ] A short session report is written to `docs/week_6_summary.md` (or `docs/week_6_partial_summary.md` if the week isn't done)
- [ ] `docs/handoff_new_session.md` is updated to point to the next week

---

## OUT OF SCOPE (do not do without asking)

- Sub-basin (HUC-8) stress overlay — this is v1.5's *other* meaning (currently v1.5 means "cooling-type classifier + retrain"). If Hiroaki wants sub-basin stress, that's a v2 task.
- Press / publicity / GitHub repo description cleanup — separate workstream
- Real-time data, API, database (v2)
- Global coverage expansion (v2)
- Optuna hyperparameter sweep — Hiroaki can run this on Colab whenever, but it's a v1.0 polish, not a v1.5 fix

---

## REPRODUCE FROM SCRATCH

```bash
cd /root/project/datacenter_water_stress

# venv + deps
test -d .venv || python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# v0 + v1.0 are shipped and idempotent. Re-running produces the same output.
# .venv/bin/python src/clean_locations.py
# .venv/bin/python src/build_wri_stress_lookup.py
# .venv/bin/python src/estimate_power.py
# .venv/bin/python src/fetch_climate.py
# .venv/bin/python src/estimate_water.py
# .venv/bin/python src/join_water_stress.py
# .venv/bin/python src/build_map.py
# .venv/bin/python src/build_ml_training_set.py
# .venv/bin/python src/build_v1_features.py
# .venv/bin/python src/v1_output_schema.py

# Week 6 work (Hiroaki picks ONE):
# Task 6.1: cooling-type classifier (recommended)
# .venv/bin/python src/build_cooling_classifier.py  (new script)
# !jupyter notebook notebooks/06_cooling_classifier.ipynb  (in Colab)
# .venv/bin/python notebooks/04_ml_training.ipynb  (re-run with new cooling_type)
# .venv/bin/python notebooks/05_v1_vs_v0_compare.py  (compare v1.5 vs v1.0)

# Task 6.2: design-day wet-bulb
# .venv/bin/python src/fetch_climate.py  (now adds wet_bulb_p99_c)
# .venv/bin/python src/estimate_water.py
# .venv/bin/python src/join_water_stress.py
# .venv/bin/python src/build_v1_features.py  (now has wet_bulb_p99_c)
# !jupyter notebook notebooks/04_ml_training.ipynb  (re-run in Colab)

# Task 6.3: PDF reconciliation
# (manually edit data/processed/ml_training_set.csv with refined values)
# .venv/bin/python src/build_ml_training_set.py
# (then re-run notebook)

# Task 6.4: Lumen/Cogent reclassification
# (edit src/estimate_power.py OPERATOR_PATTERNS)
# .venv/bin/python src/estimate_power.py
# .venv/bin/python src/estimate_water.py
# .venv/bin/python src/join_water_stress.py
# .venv/bin/python src/build_v1_features.py
# (then re-run notebook)
```

---

## OPEN QUESTIONS WITH DEFAULTS

These are the open questions at the end of Week 5. They have defaults; the next session uses the defaults unless Hiroaki redirects.

1. **Q: Which Week 6 task does Hiroaki want?**
   Default: **Task 6.1 (cooling-type classifier)** — it's the highest-impact fix and addresses the Meta LOO collapse. If Hiroaki doesn't pick, do 6.1.

2. **Q: Does Hiroaki want to ship v1.0 to the public before doing v1.5?**
   Default: **Ship v1.0 first.** The 144 B L/yr headline is the most defensible number we have. v1.5 is an improvement, not a prerequisite.

3. **Q: Should the README be updated to lead with the 144 B L/yr headline?**
   Default: **Yes, but as a "best current estimate" with v0's 237 as a "conservative upper bound".** Two numbers, both reported.

4. **Q: Should we build a v1 map (`assets/map_v1.html`)?**
   Default: **Defer to after Task 6.1.** v1.0's map would use the same Folium template as v0 with different per-facility numbers; the headline benefit is small. After v1.5, the map is more interesting because the cooling-type signal is real.

5. **Q: If Hiroaki's mid-Week-6-task and the session ends, what happens?**
   Default: write a `docs/week_6_partial_summary.md` with what's done and what's remaining, update `docs/handoff_new_session.md` to point to the partial state, leave the working tree dirty but committed. The next session picks up from the partial commit.

---

## HOW TO START THIS SESSION

1. Read this entire document.
2. Read `docs/handoff_new_session.md` (the project status snapshot).
3. **Run these four commands** to determine what state the repo is in:

   ```bash
   cd /root/project/datacenter_water_stress
   git status
   git log --oneline -5
   test -f models/water_estimator_v1.pkl && echo "v1.0 model present" || echo "v1.0 model NOT yet built"
   test -f data/processed/v1_predicted_wue.csv && echo "v1.0 predictions present" || echo "v1.0 predictions NOT yet built"
   ```

4. Based on step 3, pick the right task:
   - **v1.0 outputs present, working tree clean, no Week 6 work started** → ask Hiroaki which task (Task 6.1-6.5). If he doesn't pick, do 6.1.
   - **Working tree dirty** → inspect; might be in-progress Week 6 work. Read the latest commit to figure out state.
   - **v1.0 outputs missing** → that's a Week 5 rollback. Don't proceed; tell Hiroaki the v1.0 outputs are gone and need to be regenerated.

5. Begin the chosen task. Do not start multiple tasks in parallel; one at a time.

6. **End of session: emit a session report** to `docs/week_6_summary.md` (or `docs/week_6_partial_summary.md` if the week isn't done) listing what got built, what's open, and any questions for Hiroaki. Update `docs/handoff_new_session.md` to point to it.

**Important for the v1.5 cooling-type classifier (6.1):** This is a separate model. Don't try to bundle it into the existing `notebooks/04_ml_training.ipynb`. Make a new `notebooks/06_cooling_classifier.ipynb` and a new `src/build_cooling_classifier.py`. The WUE model in Cell 13 of `04_ml_training.ipynb` picks up the new `cooling_type` column from `v1_inference_features.csv` automatically (assuming you re-run `src/build_v1_features.py` with the new column).

**Important for the v0.5 design-day wet-bulb (6.2):** This is a forward-compatible patch. The v0 columns stay; new `wet_bulb_p99_c` and updated `climate_adj` are added. The pipeline regenerates `us_dc_with_stress.csv` from the same `us_dc_with_mw.csv` input.

---

## REMINDERS

- **Don't generate SSH keys on Hiroaki's behalf.** If the GitHub auth needs repair, walk him through `ssh-keygen` and `cat ~/.ssh/github_ed25519.pub` so he can paste the public key himself.
- **Don't run model training in Colab for Hiroaki.** The Colab session lives in his browser; you can't see it. If he's mid-run, you can't help; if he hasn't started, give him the resume prompt.
- **Don't break idempotency.** Every script in `src/` and `notebooks/` should produce the same output on re-run. Re-running is the test.
- **Don't over-claim R².** v1.0's training set is 43 rows. If v1.5 reports 0.99 R², that's a leak, not a win. The LOO test is the honest number.
- **Don't add the Open-Meteo cache to git.** It's in `.gitignore` (50 MB, regenerable). The `data/external/open_meteo/` directory is local-only.
- **Don't change the v0 columns in the v0.5 / v1.5 patches.** v0 outputs should be regenerable from the same source; the new columns are additions, not replacements. If you overwrite `wet_bulb_c` with the design-day value, the v0 pipeline breaks.
- **The 144 B L/yr headline is the most defensible number we have.** Both v0 and v1 should be reported; v1 is the "best current estimate", v0 is the "conservative upper bound". Don't pick one over the other without Hiroaki's sign-off.
