import argparse
from pathlib import Path
import pandas as pd
from scipy.io import arff
try:
    from .schema import FEATURES, CATEGORICAL, attack_class
except ImportError:
    from schema import FEATURES, CATEGORICAL, attack_class
ROOT = Path(__file__).resolve().parents[1]
def load_data(path):
    path = Path(path)
    if path.suffix.lower() == '.arff':
        records, _ = arff.loadarff(path)
        df = pd.DataFrame(records)
        df = df.map(lambda v: v.decode() if isinstance(v, bytes) else v)
        if len(df.columns) not in (42, 43): raise ValueError('Expected 41 features and label')
        df.columns = FEATURES + ['attack'] + (['difficulty'] if len(df.columns) == 43 else [])
    elif path.suffix.lower() == '.txt':
        df = pd.read_csv(path, header=None)
        if len(df.columns) not in (42, 43): raise ValueError('Expected 42 or 43 columns')
        df.columns = FEATURES + ['attack'] + (['difficulty'] if len(df.columns) == 43 else [])
    else:
        df = pd.read_csv(path)
        df = df.rename(columns={'xAttack': 'attack'})
    df['attack'] = df['attack'].map(lambda label: 'Anomaly' if str(label).lower() == 'anomaly' else attack_class(label))
    for col in FEATURES:
        if col not in CATEGORICAL: df[col] = pd.to_numeric(df[col], errors='raise')
    return df[FEATURES + ['attack']]
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=ROOT/'data/KDDTrain+.txt')
    parser.add_argument('--output', type=Path, default=ROOT/'data/processed/train.csv')
    args = parser.parse_args()
    df = load_data(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output, index=False)
    print(f'Saved {len(df)} records to {args.output}')
if __name__ == '__main__': main()
