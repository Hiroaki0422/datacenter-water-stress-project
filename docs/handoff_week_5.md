# Handoff: Water Stress Watch — Week 5 (v1 Model Training + Post-Week-4 Polish)

> **Purpose:** Self-contained prompt for a fresh Hermes session to continue the Water Stress Watch project. **Week 4 (v1 ML training foundation) is shipped and pushed to GitHub.** Week 5 is Hiroaki's interactive work on Colab Pro A100 (the actual XGBoost training), plus a small set of post-Week-4 polish items the next session can do if Hiroaki wants.
>
> Read this file once, then act.

---

## TL;DR — What to do this week

The big Week 5 deliverable is **Hiroaki's interactive Colab run** (which the next session cannot do for him — Colab credentials and the A100 GPU live in Hiroaki's browser). What the next session CAN do:

1. **Verify the Week 4 push landed correctly on GitHub** and the repo state is what we left it.
2. **If Hiroaki has finished the Colab run and pushed the v1 outputs back**, do the v0-vs-v1 comparison and ship v1.0.
3. **If Hiroaki is mid-run or hasn't started**, stand by — he doesn't need a session for the training itself.
4. **The v0.5 polish backlog** (design-day wet-bulb, Lumen/Cogent reclassification) is open and small. The next session can do these in parallel with Hiroaki's Colab work.

**The single most important thing for the next session: read the project state off disk first.** Week 4 might have been pushed, Hiroaki might have already done the v1 training and pushed the v1 outputs back, or nothing might have changed. Don't assume.

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

1. **`docs/handoff_new_session.md`** — the project status snapshot. The "What Week 4 Built" section is the most current description of what shipped.
2. **`docs/week_4_summary.md`** — what got built in Week 4, the open questions, the surprises. Skim for context.
3. **`docs/handoff_week_4.md`** — the Week 4 spec (Hiroaki's locked decisions 6-12, including the v1 ML target, training set operators, validation strategy). Read section 5 ("Hiroaki's Locked Decisions") and section 6 (Tasks 4.1-4.5) — these are the contracts.
4. **`methodology.md` Section 16** — the v1 methodology addendum. Read 16.5 (validation strategy) and 16.6 (caveats) before touching the model.
5. **`notebooks/04_ml_training.ipynb`** — the Colab notebook. The 16-cell structure is in the docstring of cell 1 and the `## v1 ML training foundation shipped` summary in `docs/handoff_new_session.md`.

> **Do NOT re-read the v0 docs (v0_plan.md, week_2_summary.md, data_dictionary.md) unless you need to.** They're historical context. If you do, use the `search_files` tool, not `read_file` end-to-end.

---

## WHAT'S ALREADY DONE (cumulative, end of Week 4)

Read these to get full context (don't re-run the pipelines):

1. `docs/v0_plan.md` — the original v0 plan, including the **v1 preview section** (lines 179-195) which is the v1 spec
2. `docs/week_2_summary.md` — what got built in Week 2 (estimation pipeline, methodology issues found)
3. `docs/data_dictionary.md` — column definitions for all 6 v0 datasets
4. `case_studies/phoenix_az.md` — the Phoenix case study (good example of how Hiroaki wants narrative content)
5. `methodology.md` — the citable methodology writeup (16 sections, 7 citations, license; Section 16 is the v1 addendum)
6. `README.md` — public intro (links the GitHub repo, the v0 map, and the Colab workflow)
7. `docs/week_4_summary.md` — Week 4 session report

**Week 4 deliverables on disk (all idempotent, all pushed to GitHub):**
- `data/processed/us_dc_with_stress.csv` — **1,575 rows × 25 columns** (the v0 inference table)
- `data/processed/ml_training_set.csv` — **43 rows × 14 columns** (the v1 training set; 42 disclosed WUE + 1 intentional NaN)
- `data/processed/v1_inference_features.csv` — **1,575 rows × 42 columns** (v0 table + 13 v1 features)
- `assets/map_v0.html` — the v0 public map (8.4 MB)
- All v0 scripts in `src/clean_locations.py` through `src/build_map.py`
- Week 4 scripts: `src/build_ml_training_set.py`, `src/build_v1_features.py`, `src/v1_output_schema.py`
- `notebooks/04_ml_training.ipynb` (16 cells, Colab Pro A100 metadata set)
- `notebooks/05_v1_vs_v0_compare.py` (post-training comparison; handles "v1 not trained yet")
- `LICENSE` (MIT), `LICENSE-data` (CC-BY 4.0)
- `.gitignore` (excludes venv, Open-Meteo cache, ATLAS, model artifacts)

---

## LOCKED DECISIONS (do not revisit without asking)

From Week 1 + Week 2 + Week 3 + Week 4 reviews (12 questions, all locked):

1. **MW estimation:** operator-class heuristic (already shipped in v0)
2. **Phoenix case study:** primary; Loudoun VA is backup (Phoenix case study shipped)
3. **License:** MIT (code), CC-BY 4.0 (data/docs), WRI Aqueduct CC-BY 4.0
4. **Stress granularity:** state-level for v0; sub-state is v1+ (NOT a Week 5 task)
5. **Source data:** only `orimadros_datacenters.csv` for v0 (1,605-row MIT)
6. **Week 4 scope:** v1 ML kickoff — skeleton + data collection only. Actual training is interactive in Colab UI by Hiroaki with A100.
7. **Colab Pro subscription** — notebook must be Colab-ready.
8. **v0.5 vs v1.0 naming:** v0.5 = bug fixes / methodology corrections; v1.0 = new model; v1.5 = sub-basin overlay; v2.0 = global.
9. **Lumen / Cogent reclassification:** wait for the v1 model. Revisit in v0.5 if v1 outputs look wrong.
10. **ML training target:** predict **WUE (L/kWh)**. At inference: `v1_water_lpd = v0_est_mw × 1000 × 24 × 0.7 × v1_predicted_wue × climate_adj`.
11. **Training set operators:** Google + Microsoft + Meta + **AWS** (region-level). Apple skipped.
12. **Validation strategy:** stratified 5-fold k-fold across all 4 operators + leave-one-operator-out generalization test.

(Full reasoning in `docs/handoff_week_4.md` near the bottom — "Hiroaki's Decisions (resolved 2026-07-04)".)

---

## THIS WEEK'S TASKS (in order)

### Task 5.1: Verify the Week 4 push is intact

The next session is a cold start. The repo state on disk and the state on GitHub may have drifted if Hiroaki pushed the v1 outputs back between sessions. Verify before doing anything else.

**Inputs:**
- `git log --oneline -5` (local)
- `git status` (local)
- `https://api.github.com/repos/Hiroaki0422/datacenter-water-stress-project/commits` (remote)

**Outputs:**
- A clear statement in your session report: "Week 4 is intact on `main` at commit X" or "Hiroaki has pushed v1 outputs; current state is commit Y with these new files".

**Acceptance criteria:**
- Local `git status` shows clean working tree OR a clear list of what changed
- Local commit is at or ahead of remote (no unpushed commits lurking)

**Code style:** just inspect; don't touch anything.

### Task 5.2: If Hiroaki has pushed v1 outputs back, run the comparison

Check whether `data/processed/v1_predicted_wue.csv` exists locally. If it does, the v1 training is done. Run:

```bash
.venv/bin/python notebooks/05_v1_vs_v0_compare.py
```

This generates `docs/v1_vs_v0_comparison.md` with the v0-vs-v1 state-level rollup and the headline "% difference by state".

**Inputs:**
- `data/processed/v1_predicted_wue.csv` (from Hiroaki's Colab push)
- `data/processed/us_dc_with_stress.csv` (v0 baseline)

**Outputs:**
- `docs/v1_vs_v0_comparison.md` (state rollup, headline numbers, caveats)

**Acceptance criteria:**
- The comparison doc has the US total v0 vs v1 numbers (e.g. "v0: 0.65 B L/day, v1: 0.71 B L/day, diff: +9%")
- The top-10 states by |v1 - v0| % difference are listed
- The file is committed and pushed

**If the file doesn't exist:** skip to Task 5.3 or 5.4. Don't synthesize the comparison.

### Task 5.3: If v1 isn't done, do one of these based on Hiroaki's instruction

Three possibilities:

a) **"Run the training for me"** — you cannot, the Colab Pro A100 lives in Hiroaki's browser. Tell him: "I can't do the GPU run; the v1 outputs are waiting on your Colab session. If you want, I can do the v0.5 design-day wet-bulb fix or the Lumen/Cogent reclassification while you train."

b) **"Reconcile the training set against the PDFs"** — open the actual operator PDFs and refine the 43-row training table. This is research-heavy, not GPU-heavy. Estimated 1-2 hours.

c) **"Do the v0.5 polish"** — see Task 5.4.

Default: ask Hiroaki which he wants. Don't guess.

### Task 5.4 (optional, if Hiroaki wants v0.5 polish): design-day wet-bulb

Replace `wet_bulb_temperature_2m_mean` (annual) with the **99th-percentile daily max wet-bulb** (or 90th, or summer-only). This is the single biggest v0 methodology issue from `docs/week_2_summary.md` — Phoenix's annual mean is 12.5°C but design-day wet-bulb is ~25°C.

**Inputs:**
- `data/external/open_meteo/batch_*.json` (16 cached Open-Meteo API responses from Week 2)
- `src/fetch_climate.py` (the script that produced the cache)

**Outputs:**
- Updated `src/fetch_climate.py` that computes `wet_bulb_design_c` (or similar) from the daily series
- Re-run `src/fetch_climate.py` → `src/estimate_water.py` → `src/join_water_stress.py` → regenerates `us_dc_with_stress.csv`
- An updated `data_dictionary.md` describing the new column
- A short addendum to `methodology.md` Section 9 (climate adjustment) explaining the change
- Push everything to GitHub as a "v0.5: design-day wet-bulb" commit

**Acceptance criteria:**
- Phoenix's new climate_adj is meaningfully different (e.g. 1.3-1.5 instead of 1.0)
- The pipeline is still idempotent
- The headline US total changes (probably 0.65 B L/day → something in the 0.8-1.0 B L/day range)
- The change is documented in the methodology

**Code style:** new column added, old column preserved (don't break v0). The v0 table can be regenerated from the same source, so this is a forward-compatible v0.5 patch.

### Task 5.5 (optional, only if Hiroaki asks): Lumen / Cogent reclassification

Per the locked decision 9, the v1 model should learn the per-operator WUE. If Hiroaki wants the v0 heuristic to be more accurate on Lumen/Cogent (the fiber+colo hybrid operators), split them into two classes with different default MWs.

**Inputs:**
- The current `src/estimate_power.py` (which classifies Lumen/Cogent as `colocation_secondary`)
- The Orimadros data for Lumen (96 rows) and Cogent (28 rows)

**Outputs:**
- An updated `OPERATOR_PATTERNS` list in `src/estimate_power.py` that splits Lumen into a `cable_telecom_lumen` or `colocation_lumen_large` class with a different default MW
- A re-run of `src/estimate_power.py` → regenerates `us_dc_with_mw.csv` and downstream
- A short note in the methodology about the reclassification

**Acceptance criteria:**
- The reclassification is defensible (cite a source, e.g. Lumen's "Enterprise" fiber + colocation split)
- The pipeline is still idempotent
- The MW total for the affected rows changes (and the headline US water total adjusts accordingly)

**Note:** this task is lower priority than Task 5.4. Only do it if Hiroaki explicitly asks, and only after Task 5.4.

---

## DONE-WHEN CHECKLIST

Week 5 is done when **at least one** of these is true:

- [ ] `docs/v1_vs_v0_comparison.md` exists and has been committed + pushed, **AND** the v1 model is in `models/water_estimator_v1.pkl` (v1.0 shipped), OR
- [ ] v0.5 polish commit is on `main` (Task 5.4 done), OR
- [ ] Hiroaki explicitly defers Week 5 work to Week 6+ (rare; if he does, write `docs/week_5_summary.md` explaining what was deferred and why, and update `docs/handoff_new_session.md`)

The session is also done when:

- [ ] `git status` is clean
- [ ] All changes are pushed to `origin/main`
- [ ] A short session report is written to `docs/week_5_summary.md` (or `docs/week_5_partial_summary.md` if the week isn't done)

---

## OUT OF SCOPE (do not do without asking)

- Optuna hyperparameter sweep — Week 6+
- Cooling-type classifier — Week 6+
- Sub-basin (HUC-8) stress overlay — Week 6+ (this is v1.5)
- Replacing the v0 map with v1 output — Week 5+ (only after v1 is validated)
- Press / publicity / GitHub repo description cleanup — separate workstream
- Real-time data, API, database (v2)
- Global coverage expansion (v2)

---

## REPRODUCE FROM SCRATCH

```bash
cd /root/project/datacenter_water_stress

# venv + deps
test -d .venv || python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# All scripts are idempotent; re-running produces the same output
# v0 pipeline (already shipped, idempotent, no need to re-run)
# .venv/bin/python src/clean_locations.py
# .venv/bin/python src/build_wri_stress_lookup.py
# .venv/bin/python src/estimate_power.py
# .venv/bin/python src/fetch_climate.py
# .venv/bin/python src/estimate_water.py
# .venv/bin/python src/join_water_stress.py
# .venv/bin/python src/build_map.py

# v1 training foundation (already shipped, idempotent, no need to re-run)
# .venv/bin/python src/build_ml_training_set.py
# .venv/bin/python src/build_v1_features.py
# .venv/bin/python src/v1_output_schema.py

# Week 5 work — the next session runs ONE of these:
.venv/bin/python notebooks/05_v1_vs_v0_compare.py     # if Hiroaki pushed v1 outputs
# (or do the v0.5 design-day wet-bulb fix per Task 5.4)

# Colab workflow (Hiroaki does this, not the session)
# git clone https://github.com/Hiroaki0422/datacenter-water-stress-project.git
# %cd datacenter-water-stress-project
# open notebooks/04_ml_training.ipynb on Colab Pro A100
# run cells 1-13, save outputs, push back

# After Hiroaki's push:
.venv/bin/python notebooks/05_v1_vs_v0_compare.py
```

---

## OPEN QUESTIONS WITH DEFAULTS

These were the open questions at the end of Week 4. They have defaults; the next session uses the defaults unless Hiroaki redirects.

1. **Q: Has Hiroaki finished the Colab training run and pushed the v1 outputs back?**
   Default: check `data/processed/v1_predicted_wue.csv` and `git log`. If yes → run Task 5.2. If no → ask Hiroaki what he wants (Task 5.3).

2. **Q: Does Hiroaki want the v0.5 design-day wet-bulb fix now, or after the v1.0 release?**
   Default: do it now if Hiroaki's not actively training. The fix is small (recompute one column from the existing Open-Meteo cache) and unblocks the v0.5 release. Defer to after v1.0 if Hiroaki is mid-training.

3. **Q: Does the v1 model need to be re-trained after the v0.5 fix?**
   Default: yes, re-run the v0.5 → v1 pipeline. The `wet_bulb_c` feature in the training set was pulled from the v0 cache; v0.5 will replace it. The model needs to learn the new feature.

4. **Q: Should the v0.5 design-day fix go into the v1 training set, or just the v0 inference table?**
   Default: both. The v0 inference table and the v1 training set both have a `wet_bulb_c` column; both need to be updated to the design-day version for consistency.

5. **Q: What if the v1 model on Colab fails (low R², NaN predictions, GPU error)?**
   Default: don't try to fix it from the VPS. Hiroaki iterates in Colab with cell-by-cell debugging. The next session writes a clear bug report (`docs/v1_training_issue_<date>.md`) and waits.

---

## HOW TO START THIS SESSION

1. Read this entire document.
2. Read `docs/handoff_new_session.md` (the project status snapshot).
3. **Run these three commands** to determine what state the repo is in:

   ```bash
   cd /root/project/datacenter_water_stress
   git status
   git log --oneline -5
   test -f data/processed/v1_predicted_wue.csv && echo "v1 outputs present" || echo "v1 outputs NOT yet pushed"
   ```

4. Based on step 3, pick the right task:
   - **v1 outputs present** → Task 5.2 (run the comparison)
   - **v1 outputs absent, working tree dirty** → inspect, decide if it's v0.5 work (Task 5.4) or junk to discard
   - **v1 outputs absent, working tree clean, no v1 outputs** → ask Hiroaki what he wants (Task 5.3)

5. Begin the chosen task. Do not start multiple tasks in parallel; one at a time.

6. **End of session: emit a session report** to `docs/week_5_summary.md` listing what got built, what's open, and any questions for Hiroaki. Update `docs/handoff_new_session.md` to point to it.

**Important for the comparison task (5.2):** The `notebooks/05_v1_vs_v0_compare.py` script handles "v1 not trained yet" gracefully (returns exit 0 with a clear message). If you run it without the v1 outputs, it'll tell you so. Don't synthesize.

**Important for the v0.5 polish task (5.4):** v0.5 is a forward-compatible patch. The v0 columns stay; new `wet_bulb_design_c` and updated `climate_adj` are added. The pipeline regenerates `us_dc_with_stress.csv` from the same `us_dc_with_mw.csv` input.

---

## REMINDERS

- **Don't generate SSH keys on Hiroaki's behalf.** If the GitHub auth needs repair, walk him through `ssh-keygen` and `cat ~/.ssh/github_ed25519.pub` so he can paste the public key himself.
- **Don't run model training in Colab for Hiroaki.** The Colab session lives in his browser; you can't see it. If he's mid-run, you can't help; if he hasn't started, give him the resume prompt below.
- **Don't break idempotency.** Every script in `src/` and `notebooks/` should produce the same output on re-run. Re-running is the test.
- **Don't over-claim R².** The v1 training set is 43 rows. If the model reports 0.99 R², that's a leak, not a win. The LOO test is the honest number.
- **Don't add the Open-Meteo cache to git.** It's in `.gitignore` (50 MB, regenerable). The `data/external/open_meteo/` directory is local-only.
