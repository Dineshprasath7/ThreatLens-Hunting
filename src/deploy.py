import math
import os
import json
import joblib
import pandas as pd
from flask import Flask, jsonify, render_template, request
try:
    from .schema import FEATURES, CATEGORICAL
    from .preprocess import ROOT
except ImportError:
    from schema import FEATURES, CATEGORICAL
    from preprocess import ROOT
MAPPINGS = {
    'Normal': ('Info', None, None),
    'DoS': ('High', 'T1498', 'Network Denial of Service'),
    'Probe': ('Medium', 'T1046', 'Network Service Discovery'),
    'R2L': ('High', 'T1110', 'Brute Force'),
    'U2R': ('Critical', 'T1068', 'Exploitation for Privilege Escalation')}
MAPPING_CONTEXT = {
    'Normal': ('No ATT&CK technique', 'No attack behavior was inferred. Continue normal monitoring; a Normal prediction does not prove safety.'),
    'DoS': ('Availability / Impact', 'Look for traffic spikes, repeated connections, service errors, and affected availability.'),
    'Probe': ('Discovery', 'Correlate with sequential port or service attempts across hosts and network scan telemetry.'),
    'R2L': ('Remote access / Credential Access', 'Check authentication logs, failed logins, account context, and unexpected remote access. R2L includes more than brute force.'),
    'U2R': ('Privilege Escalation', 'Correlate with host process, privilege, exploit, and account telemetry. A network record alone cannot establish exploitation.')
}
def validate(record):
    if not isinstance(record, dict): raise ValueError('Each connection must be an object')
    missing, extra = set(FEATURES)-record.keys(), record.keys()-set(FEATURES)
    if missing: raise ValueError('Missing features: ' + ', '.join(sorted(missing)))
    if extra: raise ValueError('Unknown features: ' + ', '.join(sorted(extra)))
    for key, value in record.items():
        if key in CATEGORICAL:
            if not isinstance(value, str) or not value.strip(): raise ValueError(f'{key} must be a nonempty string')
            if key == 'protocol_type' and value not in ('tcp', 'udp', 'icmp'): raise ValueError('protocol_type must be tcp, udp, or icmp')
        elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f'{key} must be a finite nonnegative number')
        elif key.endswith('_rate') and value > 1: raise ValueError(f'{key} must be between 0 and 1')

def create_app(model_path=None):
    app = Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
    path = model_path or os.environ.get('THREATLENS_MODEL', ROOT/'models/threatlens.joblib')
    bundle = joblib.load(path) if PathExists(path) else None
    @app.get('/health')
    def health():
        return jsonify(status='ready' if bundle else 'model_missing'), 200 if bundle else 503
    @app.get('/schema')
    def schema():
        return jsonify(features=FEATURES, categorical=CATEGORICAL, batch_limit=100)
    @app.get('/metrics')
    def metrics():
        if bundle is None: return jsonify(error='Train the model first'), 503
        return jsonify(bundle['metadata'])
    @app.get('/api-docs')
    def api_docs():
        example = json.loads((ROOT / 'examples/dos.json').read_text(encoding='utf-8'))
        return render_template('api_docs.html', features=FEATURES, categorical=CATEGORICAL, example=example)
    @app.get('/mitre')
    def mitre_page():
        mappings = []
        for label, (severity, technique, name) in MAPPINGS.items():
            tactic, hunting_note = MAPPING_CONTEXT[label]
            mappings.append(dict(label=label, severity=severity, technique=technique,
                                 name=name, tactic=tactic, hunting_note=hunting_note,
                                 url=f'https://attack.mitre.org/techniques/{technique}/' if technique else None,
                                 recall=bundle['metadata']['classification_report'][label]['recall'] if bundle else None))
        return render_template('mitre.html', mappings=mappings)
    @app.get('/')
    @app.get('/predict')
    def demo():
        examples = {
            label: json.loads((ROOT / f'examples/{label}.json').read_text(encoding='utf-8'))
            for label in ('normal', 'dos', 'probe', 'r2l', 'u2r')
        }
        return render_template('predict.html', examples=examples, model_ready=bundle is not None)
    @app.post('/predict')
    def predict():
        if bundle is None: return jsonify(error='Train the model first'), 503
        if not request.is_json: return jsonify(error='Content-Type must be application/json'), 415
        data = request.get_json(silent=True)
        records = data if isinstance(data, list) else [data]
        try:
            if not 1 <= len(records) <= 100: raise ValueError('Supply 1 to 100 connections')
            for record in records: validate(record)
        except ValueError as error:
            return jsonify(error=str(error)), 400
        pipeline = bundle['pipeline']
        probabilities = pipeline.predict_proba(pd.DataFrame(records)[FEATURES])
        classes = pipeline.classes_
        results = []
        for probabilities_row in probabilities:
            label = str(classes[probabilities_row.argmax()])
            severity, technique, name = MAPPINGS[label]
            results.append(dict(prediction=label, confidence=float(probabilities_row.max()), severity=severity,
                probabilities={str(c): float(v) for c, v in zip(classes, probabilities_row)},
                mitre_attack={'technique': technique, 'name': name, 'url': f'https://attack.mitre.org/techniques/{technique}/' if technique else None,
                              'mapping_type': 'illustrative category-level association'}))
        return jsonify(results=results, confidence_note='Random Forest vote proportion; not calibrated certainty')
    return app

def PathExists(path):
    from pathlib import Path
    return Path(path).is_file()
if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
