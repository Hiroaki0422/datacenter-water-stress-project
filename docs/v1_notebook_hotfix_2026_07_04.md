# Hotfix: 04_ml_training.ipynb Cell 13 — schema mismatch (2026-07-04)

**Bug:** Cell 13 crashed with `KeyError: "None of [Index(['cooling_type', 'operator', 'is_aggregate'], dtype='object')] are in the [columns]"`.

**Root cause:** The training set (`ml_training_set.csv`) and the inference set (`v1_inference_features.csv`) have different column names. The training set has `cooling_type`, `operator`, `is_aggregate` (from operator disclosures). The inference set has `operator_class` (one-hot) + `provider` (raw) but NOT `cooling_type` (v0 didn't capture it) or `is_aggregate` (training-set only).

**Fix:** Commit `69e2735` on `main` (pushed). Cell 13 now synthesizes the missing columns before one-hot encoding.

## What Hiroaki does on Colab

```python
# In the Colab session, FIRST run this to pull the fix:
!cd /content/wsw && git pull origin main
# or if you cloned fresh: re-clone.

# Then re-run the notebook from Cell 1.
# Cell 13 should now print:
#   Inference matrix shape: (1575, 11)  (expected: (1575, 11))
#   NaN count in reindexed matrix: 0
# And the predicted WUE stats follow.

# If you ALREADY ran cells 1-12 successfully and just need to re-run 13:
# (Cells 1-12 don't need to re-run; just re-run cell 13)
```

## The semantic caveat (read this before trusting the predictions)

The fix makes the column shapes match, but the **operator encoding in the inference matrix is a proxy, not a literal match**. Specifically:

| In the inference matrix | What the model thinks |
|---|---|
| `operator_Google = 1` | "This is a hyperscaler_self facility" (because `operator_map` mapped `hyperscaler_self → "Google"`) |
| `operator_AWS = 0` | "This is NOT an AWS region aggregate" — but every inference row is `is_aggregate=False`, so this is trivially true |
| `operator_Meta = 0` | "This is NOT a Meta dry-cooled site" — but the model has never seen a Meta dry-cooled site in the inference matrix |
| `cooling_type_unknown = 0`, `cooling_type_air = 0`, `cooling_type_evaporative = 0` | "This facility has no cooling-type signal" — the model treats it as a "no cooling" case |

**Practical consequence:** A colocation_major facility (e.g. Equinix Ashburn) will get the same predicted WUE as a similar-latitude AWS region, because both have `operator_* = 0` except for the mapped one (`operator_Equinix = 1` in inference, `operator_Comcast = 1` for cable_telecom rows, etc.).

**If you want better predictions for non-hyperscaler facilities, two options:**

1. **Re-train the model with operator_class one-hots directly.** Modify Cell 7 to add `is_hyperscaler_self`, `is_colocation_major`, etc. to `X`. The training set doesn't have these columns, so you'd need to add them to `ml_training_set.csv` (deterministic from the `operator` column via a mapping table) OR change Cell 7 to engineer them on the fly from the operator string.

2. **Wait for v1.5 (cooling-type classifier).** A separate model that predicts cooling type from lat/lon + sqft would let the v1 model use cooling_type as a real signal, not a constant "unknown".

**For the v1.0 first run, this is acceptable.** The model is still better than the v0 flat constant (which has no operator or cooling signal at all). The 4 known operators (Google/Microsoft/Meta/AWS) get distinct predictions; the rest get a "generic" prediction. Once the cooling-type classifier ships (v1.5), this issue goes away.

## Files changed

- `notebooks/04_ml_training.ipynb` (Cell 13 only)

## Verification (local)

```
Training matrix: (42, 11)
Inference matrix (before reindex): (1575, 11)
After reindex: (1575, 11)
NaN count: 0
All columns align: True
```
