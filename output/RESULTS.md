# ThreatLens run and requirements check

Run date: 13 October 2026 (Asia/Kolkata). Python 3.13.6, scikit-learn 1.6.1, pinned dependencies from `requirements.txt` in `.venv`.

## Commands run

`run.bat -Mode All -NoServe` — passed end to end on 13 October 2026: ARFF conversion, training, five automated tests, and all five example predictions. The `Test` toggle also passed independently.


`python -m src.preprocess --input data/KDDTrain+.arff --output output/arff_converted.csv` — passed; 125,973 rows written. Bundled ARFF labels are binary Normal/Anomaly, so five-class training uses the bundled TXT datasets.

`python -m src.train` — passed; 125,973 training rows and 22,544 official held-out test rows. Model saved to `models/threatlens.joblib`; reports regenerated in `reports/`.

`python -m unittest discover -s tests -v` — 5 tests passed (input validation, class mapping, missing model, batch inference, unseen service).

`python -m src.predict examples/dos.json` — returned DoS, confidence 1.00, High severity, T1498.

Live Flask server at `127.0.0.1:5000`: `curl.exe --noproxy "*" http://127.0.0.1:5000/health` returned HTTP 200 and `{"status":"ready"}`. POST requests to `/predict` with all five example JSON files succeeded.

## Held-out test results

Accuracy: **73.70%**. Macro precision 70.51%, macro recall 47.40%, macro F1 47.72%.

| Actual class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Normal | 63.39% | 97.26% | 76.75% | 9711 |
| DoS | 96.14% | 76.54% | 85.23% | 7460 |
| Probe | 85.88% | 60.06% | 70.69% | 2421 |
| R2L | 57.14% | 0.14% | 0.28% | 2885 |
| U2R | 50.00% | 2.99% | 5.63% | 67 |

Confusion matrix (rows actual, columns predicted):

| Actual \ Predicted | Normal | DoS | Probe | R2L | U2R |
|---|---:|---:|---:|---:|---:|
| Normal | 9445 | 67 | 198 | 0 | 1 |
| DoS | 1717 | 5710 | 33 | 0 | 0 |
| Probe | 805 | 162 | 1454 | 0 | 0 |
| R2L | 2872 | 0 | 8 | 4 | 1 |
| U2R | 62 | 0 | 0 | 3 | 2 |

The model misses nearly all R2L and U2R records. Overall accuracy should not be presented as strong detection for those classes. Predictions on representative held-out examples: Normal→Normal (1.00), DoS→DoS (1.00), Probe→Probe (0.891), R2L→Normal (0.933), U2R→Normal (0.787). Confidence is the Random Forest vote proportion, not calibrated probability of correctness.

## Original summary verification

| Requirement | Status | Evidence / limit |
|---|---|---|
| NSL-KDD five-class Normal, DoS, Probe, R2L, U2R classification | Implemented, weak on rare classes | TXT training labels map to five classes; held-out report above shows poor R2L/U2R recall. |
| Raw ARFF to CSV | Implemented | Conversion generated `output/arff_converted.csv`; ARFF labels are binary, so cannot themselves support five-class training. |
| Label encoding and feature preprocessing | Implemented | `src/preprocess.py` maps labels; persisted scikit-learn ordinal encoder transforms protocol, service, flag; numeric features are validated. |
| Random Forest training and reusable model | Implemented | `src/train.py` regenerated `models/threatlens.joblib` with preprocessing and classifier. |
| Flask REST `/predict` accepting connection features and confidence | Implemented | Live curl POSTs succeeded; all 41 NSL-KDD features required. |
| Real-time classification | Partial | HTTP inference is immediate for supplied feature objects. No packet capture, traffic stream, or automatic extraction of NSL-KDD features exists. |
| MITRE ATT&CK and severity | Implemented as illustrative mapping | DoS T1498/High, Probe T1046/Medium, R2L T1110/High, U2R T1068/Critical; Normal/Info. A class does not prove a specific technique. |
| Accuracy, precision, recall, F1, per-class confusion matrix | Implemented | Tables above and generated `reports/` files. |
| curl/Postman | curl verified; Postman not separately run | Live curl request confirmed API. The same JSON body can be sent in Postman per README. |
| Python, pandas, scikit-learn, Flask, joblib | Verified | Dependencies installed from `requirements.txt`; pipeline and API executed. |

## Reproduce

From the project root, activate `.venv` and run `python -m src.train`, `python -m unittest discover -s tests -v`, then `python -m src.deploy`. In another terminal, run `curl.exe --noproxy "*" -X POST http://127.0.0.1:5000/predict -H "Content-Type: application/json" --data-binary "@examples/dos.json"`.

Source project and license are identified in `README.md` and `LICENSE`.
