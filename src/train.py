import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import joblib
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
try:
    from .schema import FEATURES, CATEGORICAL, CLASSES
    from .preprocess import load_data, ROOT
except ImportError:
    from schema import FEATURES, CATEGORICAL, CLASSES
    from preprocess import load_data, ROOT

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', type=Path, default=ROOT/'data/KDDTrain+.txt')
    parser.add_argument('--test', type=Path, default=ROOT/'data/KDDTest+.txt')
    parser.add_argument('--trees', type=int, default=150)
    args = parser.parse_args()
    train, test = load_data(args.train), load_data(args.test)
    if 'Anomaly' in set(train.attack) | set(test.attack):
        raise ValueError('Binary ARFF labels cannot recover five attack classes; use the bundled TXT files')
    pipeline = Pipeline([
        ('preprocess', ColumnTransformer([('categories', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1), CATEGORICAL)], remainder='passthrough')),
        ('classifier', RandomForestClassifier(n_estimators=args.trees, random_state=42, n_jobs=-1, class_weight='balanced_subsample'))])
    pipeline.fit(train[FEATURES], train.attack)
    predicted = pipeline.predict(test[FEATURES])
    report = classification_report(test.attack, predicted, labels=CLASSES, output_dict=True, zero_division=0)
    result = {'accuracy': accuracy_score(test.attack, predicted), 'classification_report': report,
              'classes': CLASSES, 'confusion_matrix': confusion_matrix(test.attack, predicted, labels=CLASSES).tolist(),
              'train_records': len(train), 'test_records': len(test), 'evaluation': 'Official NSL-KDD held-out test set',
              'sklearn_version': sklearn.__version__, 'trained_at': datetime.now(timezone.utc).isoformat()}
    (ROOT/'models').mkdir(exist_ok=True)
    (ROOT/'reports').mkdir(exist_ok=True)
    joblib.dump({'pipeline': pipeline, 'metadata': result}, ROOT/'models/threatlens.joblib', compress=3)
    (ROOT/'reports/metrics.json').write_text(json.dumps(result, indent=2))
    import pandas as pd
    pd.DataFrame(result['confusion_matrix'], index=CLASSES, columns=CLASSES).to_csv(ROOT/'reports/confusion_matrix.csv', index_label='actual / predicted')
    pd.DataFrame(report).transpose().to_csv(ROOT/'reports/classification_report.csv')
    (ROOT/'examples').mkdir(exist_ok=True)
    for label in CLASSES:
        sample = test.loc[test.attack == label, FEATURES].iloc[0].to_dict()
        (ROOT/f'examples/{label.lower()}.json').write_text(json.dumps(sample, indent=2))
    print(json.dumps(result, indent=2))
if __name__ == '__main__': main()
