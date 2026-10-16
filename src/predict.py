import argparse
import json
try:
    from .deploy import create_app
    from .preprocess import ROOT
except ImportError:
    from deploy import create_app
    from preprocess import ROOT
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?', default=str(ROOT/'examples/normal.json'))
    args = parser.parse_args()
    with open(args.input) as source: data = json.load(source)
    response = create_app().test_client().post('/predict', json=data)
    print(json.dumps(response.get_json(), indent=2))
    raise SystemExit(0 if response.status_code == 200 else 1)
