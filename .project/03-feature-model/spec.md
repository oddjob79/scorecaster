# 03 Feature model

## Goal

Find out whether the pre-match feature table improves on the baseline goals model, and keep only the features that do.

## Why

- The feature table holds about 150 columns on intuition: form, head to head, position bands, Elo, streaks.
- Many of them overlap. Most add nothing once team strength is known, and some add noise.

## Shape of the solution

- **Input:** `v_match_features` (one row per match), plus the shot and odds-derived columns from phase 01.
- **Models, simplest first:**
  - Poisson regression on each team's goals, with the features as inputs. It stays a goals model, so every market comes out of it as in phase 02.
  - LASSO (regression that shrinks unhelpful features to zero) to pick out the features that matter.
  - Gradient boosting (many small decision trees added together) with SHAP (a method that shows how much each feature moved a prediction), if the regressions plateau.
- **Comparison:** same walk-forward split and scores as phase 02. A feature model is kept only if it beats Dixon-Coles on log-loss.
- **Output:** rows in the same predictions table, tagged with the model name.
- **Feature report:** which features survive and how much each contributes.

## Open questions

- Use the Dixon-Coles strengths as input features (stacking), or compete against them?
- Predict goals (then derive markets), or predict H/D/A directly with multinomial logistic regression?
- Which libraries: statsmodels, scikit-learn, LightGBM, shap? Each needs permission to install.

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- Poisson regression on goals with features
- LASSO feature selection
- walk-forward comparison against the baseline
- predictions written to the shared table

**Optional**

- gradient boosting with SHAP (new model module)
- probability calibration step, such as isotonic regression (model wrapper)
- feature-importance report (analysis notebook)
- stacking Dixon-Coles strengths into the features (feature input)
- pruning the calculators that never survive selection (`features/calculators.py`)
