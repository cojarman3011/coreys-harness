# Skylinee Linear v1.0 — From classroom model to portable inference service

**Author:** Corey W. Jarman · **Organization:** Skylinee LLC

A small original application workflow around standard linear regression: numeric CSV training, deterministic train/test evaluation, portable JSON model serialization (no joblib/pickle), SHA-256 and independently pinned prediction-reference release checks, extrapolation warnings, and local HTTP inference. It is designed to run on standard Python on Raspberry Pi and Linux once a model has been trained.

**What is original here:** the Skylinee packaging, schema checks, independent release-policy workflow, CLI, reference-vector construction, and inference API. Ordinary and ridge least-squares regression are established algorithms, **not** claimed as novel mathematics. The original 30-point training exercise is illustrative and must not be marketed as a real-world trained predictor.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
python -m pip install -e '.[train]'

python -m skylinee_linear train --csv examples/sample_realistic.csv --target hours --features work_units --model model.json --policy release_policy.json
python -m skylinee_linear verify --model model.json --policy release_policy.json
python -m skylinee_linear predict --model model.json --policy release_policy.json --features-json '{"work_units":9}'
python -m skylinee_linear serve --model model.json --policy release_policy.json
```

Then in a second terminal:

```bash
curl http://127.0.0.1:5055/health
curl http://127.0.0.1:5055/schema
curl -H 'Content-Type: application/json' -d '{"features":{"work_units":9}}' http://127.0.0.1:5055/predict
curl -H 'Content-Type: application/json' -d '{"rows":[{"work_units":9},{"work_units":10}]}' http://127.0.0.1:5055/batch
```

**Important:** the included CSV contains **fictional demonstration measurements**. Replace it with authentic, appropriately consented/lawful data. An estimate is not an operational commitment.

## Train your own dataset

Provide a CSV with numeric column headers, at least 12 complete rows, and one numeric target. Up to 32 numeric features are supported. Default uses a fitted intercept, 20% deterministic random holdout, and an ordinary-least-squares solution. For multiple features:

```bash
python -m skylinee_linear train --csv measurements.csv --target result --features x1 x2 x3 --model results/my_model.json --policy results/approved_policy.json
```

A second model can be trained with `--no-intercept` to reproduce the classroom **constraint**, not as the recommended default. Use `--ridge 1.0` for optional L2 regularization. Training uses `numpy.linalg.lstsq`; prediction and verification need only Python standard library.

The tool returns holdout MAE, RMSE, and R² (R² may be null if the holdout target is constant). These are **single split** estimates, not cross-validated accuracy or confidence intervals. Missing and nonfinite values cause a clear error rather than silent data cleaning.

## The verified release boundary

1. `train` creates a portable numeric `model.json` and a **separate** `release_policy.json` with an artifact SHA-256 plus four reference predictions, including one beyond training feature ranges.
2. `verify` and `serve` refuse an artifact whose bytes or predictions do not match its policy. The policy uses explicit `math.isclose` relative and absolute tolerances of `1e-9`; these values are convenience defaults **not empirically certified portability bounds**.
3. **Critical trust condition:** The policy must be protected from the party or automated agent that proposes the model. If the same person/agent can change both JSON files, the digest alone offers no meaningful provenance guarantee. Approve and store the policy outside the proposed artifact's write permissions.
4. JSON serialization deliberately avoids executing arbitrary code from untrusted pickle/joblib models. Do not load old joblib files from untrusted origins.
5. Version-independent inference does **not** prove equivalent numerical behavior across CPU architectures; compare reference vectors against the original trusted training environment for a real migration study.

This gate proves *identity relative to the approved policy* and sampled parity under the stated tolerance. It does not establish correct data labeling, unbiased predictions, generalization, complete protection against tampering, or safety for consequential decisions.

## Reproducing the original classroom numerical example

Run `python examples/recreate_classroom.py` after installing NumPy. It generates exactly 30 synthetic points using `RandomState(10)`, prints the full-data forced-zero-intercept slope, and writes `classroom_30.csv`. This should produce approximately `2.35864031` and `14.15184187` at x=6, consistent with the corrected research report.

**Why training this project on `classroom_30.csv` differs:** Unlike the original classroom code (which trained on all 30 points), Skylinee Linear holds out 20% for honest evaluation by default, so its fit uses fewer points. The historic model had no held-out evaluation.

## Running on the Raspberry Pi

Copy the complete folder to the Pi, then install the package *without* training dependencies (`pip install -e .`); training on x86 and deploying the portable JSON to ARM64 is supported at the application level, without deserializing scikit-learn objects. Carry the approved `release_policy.json` over a trusted channel. Run `python -m skylinee_linear serve --model ... --policy ...` and use SSH tunneling or a secured reverse proxy.

The HTTP server binds to `127.0.0.1` by default. It has **no user authentication, authorization, rate limiting, or TLS**. Never expose it directly to the public internet. Use suitable controls (e.g., your existing Apache + TLS, authentication, access logging and network restrictions).

## Tests

```bash
python -m unittest discover -s tests -v
```

## Limits and provenance

- Original model: scikit-learn `LinearRegression(fit_intercept=False)`, 30 seeded synthetic samples, 517-byte joblib file. This package is **an upgrade in application functionality**, not a bit-for-bit re-export of the historical joblib model.
- No claim of novel statistical estimator, autonomous learning or recursive self-improvement.
- Retraining is a manually invoked operation; no online learning or adaptive decisions occur automatically.
- All software is provided as an educational and general-purpose numerical estimation reference, not as a validated medical, financial, security, or safety-critical decision system.

## License

Apache License 2.0 applies to this Skylinee application code, consistent with the existing Coreys Harness repository. Third-party scientific libraries are separately licensed. The research paper and user data are not included or relicensed by this repository.