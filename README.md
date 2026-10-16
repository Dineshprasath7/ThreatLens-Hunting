# ThreatLens

Five-class NSL-KDD intrusion classification with Random Forest, persisted preprocessing, Flask inference, and held-out evaluation.

## One-command runner

On Windows, run `run.bat -Mode All` (or double-click `run.bat`) to convert ARFF, train, test, demo all five examples, and start the API. Use `run.bat -Mode All -NoServe` for a full check that exits, or choose `-Mode Train`, `Test`, `Demo`, or `Serve`. PowerShell: `.\run.ps1 -Mode All`. See the [showcase guide](output/SHOWCASE.md) and [verified results](output/RESULTS.md).

After code changes, stop the earlier server with Ctrl+C and start it again. The runner reports when port 5000 is already occupied; an older server can otherwise keep serving outdated routes.

## Run

From this folder (Python 3.11-3.13):

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m src.preprocess
.\.venv\Scripts\python -m src.train
.\.venv\Scripts\python -m unittest discover -s tests
.\.venv\Scripts\python -m src.deploy
```

Training uses KDDTrain+.txt; evaluation uses the official separate KDDTest+.txt. The difficulty field is excluded. Training-fitted categorical encoders are persisted with the classifier; unseen service/flag strings encode as -1. The classifier returns Normal, DoS, Probe, R2L, or U2R.

ARFF to CSV: `python -m src.preprocess --input data/KDDTrain+.arff --output data/processed/train.csv`. ARFF expects the standard NSL-KDD 41-feature order plus textual label. Bundled ARFF files have binary normal/anomaly labels; conversion preserves Anomaly, but five-class training requires the TXT files. CSV expects named features and textual `attack` or `xAttack`.

## API and Postman

Open `http://127.0.0.1:5000/predict` in a browser for an interactive demo. Select a sample and click **Predict connection**; the page sends the required JSON POST. Typing the URL alone sends GET and displays the demo page.

Open `http://127.0.0.1:5000/api-docs` for endpoint and feature documentation, and `http://127.0.0.1:5000/mitre` for the five category mappings, severity, hunting notes, and measured per-class recall. These pages are linked from the prediction demo.

```powershell
curl.exe http://127.0.0.1:5000/health
curl.exe -X POST http://127.0.0.1:5000/predict -H "Content-Type: application/json" --data-binary "@examples/normal.json"
curl.exe -X POST http://127.0.0.1:5000/predict -H "Content-Type: application/json" --data-binary "@examples/dos.json"
```

For Postman: POST to http://127.0.0.1:5000/predict with raw JSON copied from an example. Supply all 41 features; categories use strings, not encoded numbers. Key order does not matter. Accepts one object or a list of 1-100 objects. `/schema` documents features, `/metrics` returns evaluation, and `/health` returns readiness. Offline demo: `python -m src.predict examples/probe.json`.

Response `results` entries contain prediction, confidence, per-class probabilities, severity, and MITRE context. Confidence is vote proportion, not calibrated certainty. Invalid input returns 400, non-JSON returns 415, missing model returns 503. Example filenames indicate ground truth, not guaranteed predictions.

## Reports and limits

Training creates models/threatlens.joblib and reports/metrics.json, classification_report.csv, confusion_matrix.csv. Reports contain accuracy, precision, recall, F1, support, macro/weighted averages, and confusion matrix (actual rows, predicted columns). Inspect rare R2L/U2R recall alongside accuracy. Only load trusted joblib files.

Illustrative category associations: [DoS T1498](https://attack.mitre.org/techniques/T1498/), [Probe T1046](https://attack.mitre.org/techniques/T1046/), [R2L T1110](https://attack.mitre.org/techniques/T1110/), [U2R T1068](https://attack.mitre.org/techniques/T1068/). These are contextual associations, not proof of an observed technique. R2L includes attacks beyond brute force. Severity is a project-defined policy.

This API performs synchronous inference on supplied features. It does not capture network packets or compute NSL-KDD connection/window statistics. A live sensor must derive these features consistently. NSL-KDD is a historical benchmark; results do not demonstrate modern production detection quality. Malware/phishing detection is not supported.
