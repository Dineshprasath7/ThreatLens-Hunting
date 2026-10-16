# ThreatLens showcase guide

## Lead with this

“ThreatLens takes a structured NSL-KDD connection record, classifies it as Normal, DoS, Probe, R2L, or U2R, and returns analyst context through a Flask API. I evaluated it on the separate official test set, including its failures.”

Credit the [MIT-licensed starter](https://github.com/mahaswetaroy1/cybersecurity-threat-ai) and explain the additions: consistent preprocessing, five-class grouping, held-out evaluation, validated API, MITRE context, tests, and the runner.

## Three-minute walkthrough

1. **Problem (20 seconds):** Analysts need a triage signal for suspicious connection records. Explain the five groups and that this is a supervised benchmark model.
2. **Pipeline (45 seconds):** Show `src/preprocess.py` and `src/train.py`. There are 41 features including duration, protocol, service, flags, byte counts, and connection statistics. The category encoder is fitted on training data and saved with the Random Forest so the API uses identical transformations. Bundled ARFF has only binary Normal/Anomaly labels; five-class training uses the TXT files.
3. **Evaluation (45 seconds):** Open `output/RESULTS.md`. There are 125,973 training records and 22,544 separate test records. Accuracy is 73.70%. Show recall: DoS 76.54%, Probe 60.06%, R2L 0.14%, U2R 2.99%. The last two are serious gaps.
4. **API demo (45 seconds):** Start `run.bat -Mode Serve`; open `http://127.0.0.1:5000/predict` in a browser, choose DoS, and click **Predict connection**. Explain prediction, confidence, severity, and T1498. The page sends a JSON POST to the same route. Open `/api-docs` for the request contract and `/mitre` for all category mappings and recall. A malformed request returns an error.
5. **Threat hunting interpretation (25 seconds):** ATT&CK IDs are illustrative category associations. A hunter should correlate a prediction with traffic, asset context, and other alerts before concluding that a technique occurred.

## Demo commands

In Command Prompt, run `run.bat -Mode All` to convert, train, test, show five examples, and start the API. In another terminal:

```bat
curl.exe --noproxy "*" http://127.0.0.1:5000/health
curl.exe --noproxy "*" -X POST http://127.0.0.1:5000/predict -H "Content-Type: application/json" --data-binary "@examples/dos.json"
```

For a fast demo after training, run `run.bat -Mode Serve`. To run all checks and exit, use `run.bat -Mode All -NoServe`. Other modes: `Train`, `Test`, and `Demo`. PowerShell users can run `.\run.ps1 -Mode Serve`; the batch wrapper handles process-local execution policy.

The example filenames indicate their true labels, not guaranteed predictions. The R2L and U2R example records currently predict Normal. Do not use one high-confidence DoS result to claim strong detection for every class.

## Questions to prepare for

- **Is it live network detection?** It performs immediate inference on supplied features. It does not capture packets or derive the connection statistics. A sensor and feature extractor would be needed.
- **Why use a separate test set?** The encoder and model never fit it. It also exposes some train/test distribution shift.
- **Why poor R2L/U2R recall?** The categories are rare or difficult and the forest often predicts Normal. Possible next work: class-specific feature analysis, validation-set threshold tuning, training-only resampling, and testing on newer datasets. Evaluate changes on untouched data.
- **What is confidence?** A Random Forest vote proportion, not a calibrated probability of correctness.
- **Does the MITRE mapping prove a technique?** No. Broad classes cover several behaviors; the mapping starts analyst investigation.
- **What is the contribution?** A reproducible educational pipeline and honest evaluation, not a new intrusion detection algorithm. Distinguish additions here from the starter and NSL-KDD benchmark.

Emphasize the full record-to-triage flow, saved preprocessing, reproducible metrics, per-class failure analysis, and the gap between this benchmark API and a deployable threat hunting sensor.
