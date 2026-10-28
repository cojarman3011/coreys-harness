# Skylinee Linear v1.0

**Author:** Corey W. Jarman · **Skylinee LLC** · Apache License 2.0 (repository license)

A reusable Python application that converts numeric CSV data into a linear or ridge regression model, evaluates it on a held-out test split, exports a portable JSON artifact and release policy, checks model integrity and reference predictions, and serves predictions through a local HTTP interface.

This is an original **application workflow** by Skylinee, not a claim to have invented linear regression, ridge regression or model hashing. The original scikit-learn 30-row teaching exercise is separately reproducible, but is not claimed as a validated real-world prediction model.

## Install

```bash
cd experiments/skylinee-linear
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e '.[train]'
```

## Train, verify, predict

```bash
python -m skylinee_linear train --csv examples/sample_realistic.csv --target hours --features work_units --model model.json --policy release_policy.json
python -m skylinee_linear verify --model model.json --policy release_policy.json
python -m skylinee_linear predict --model model.json --policy release_policy.json --features-json '{"work_units":9}'
python -m skylinee_linear serve --model model.json --policy release_policy.json
```

Then send `POST http://127.0.0.1:5055/predict` with header `Content-Type: application/json` and body `{"features":{"work_units":9}}`. Routes: `GET /health`, `GET /schema`, `POST /predict`, `POST /batch`.

For real use, replace the **fictional sample CSV** with actual numeric measurements. Multiple numeric columns are supported by passing more feature names after `--features`. The baseline has a fitted intercept; `--no-intercept` reproduces the classroom constraint. `--ridge 1.0` enables L2 regularization. The holdout is a deterministic randomized 20% split by default (not cross-validation).

## Validate the code

```bash
python -m unittest discover -s tests -v
python examples/recreate_classroom.py
```

The historical full-30 zero-intercept fit gives slope approximately **2.35864031** and prediction at x=6 of **14.15184187**. Training with the new CLI holds back test rows, so its fitted model is not identical to the old one.

## Verification and limitations

The training workflow creates `model.json` and a separate `release_policy.json` with a SHA-256 digest and four test vectors (including extrapolation). The policy is only a trusted verifier if it is approved and stored independently of the candidate model. A person or agent allowed to rewrite both files can defeat the check. The reference vectors test only selected behaviors; no guarantee of overall predictive accuracy, fairness or generalization is implied.

Inference and verification require only the Python standard library; NumPy is required for training. The JSON representation avoids executing untrusted joblib or pickle bytes. The HTTP interface defaults to **127.0.0.1**, and provides **no authentication or TLS**. Do not expose it directly to the Internet; use an authenticated reverse proxy and network isolation.

The example is for general numerical estimation and research, **not safety-critical decision making**. No autonomous retraining, recursive improvement or cross-platform parity benchmark is claimed.
