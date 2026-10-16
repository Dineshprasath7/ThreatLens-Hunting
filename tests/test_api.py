import json
import unittest
from src.deploy import create_app
from src.preprocess import ROOT, load_data
from src.schema import FEATURES, attack_class
class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = create_app().test_client()
        cls.sample = json.loads((ROOT/'examples/normal.json').read_text())
    def test_prediction_and_batch(self):
        response = self.client.post('/predict', json=[self.sample, self.sample])
        self.assertEqual(response.status_code, 200)
        results = response.get_json()['results']
        self.assertEqual(len(results), 2)
        self.assertAlmostEqual(sum(results[0]['probabilities'].values()), 1)
    def test_browser_demo_and_api(self):
        page = self.client.get('/predict')
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'Predict connection', page.data)
        self.assertIn(b'examples', page.data)
        response = self.client.post('/predict', json=self.sample)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['results'][0]['prediction'], 'Normal')
    def test_reference_pages_share_api_mapping(self):
        docs = self.client.get('/api-docs')
        self.assertEqual(docs.status_code, 200)
        self.assertIn(b'POST /predict', docs.data)
        self.assertIn(b'duration', docs.data)
        mapping = self.client.get('/mitre')
        self.assertEqual(mapping.status_code, 200)
        for value in (b'T1498', b'T1046', b'T1110', b'T1068'):
            self.assertIn(value, mapping.data)
        self.assertIn(b'0.14%', mapping.data)
    def test_invalid_inputs(self):
        for data in ({}, [], None, {**self.sample, 'duration': -1}, {**self.sample, 'extra': 1}, {**self.sample, 'serror_rate': 2}):
            self.assertEqual(self.client.post('/predict', json=data, content_type='application/json').status_code, 400)
    def test_unknown_service(self):
        self.assertEqual(self.client.post('/predict', json={**self.sample, 'service': 'unseen_service'}).status_code, 200)
    def test_missing_model(self):
        self.assertEqual(create_app(ROOT/'models/absent.joblib').test_client().get('/health').status_code, 503)
    def test_labels(self):
        self.assertEqual(attack_class('neptune'), 'DoS')
        self.assertEqual(attack_class('xterm'), 'U2R')
        with self.assertRaises(ValueError): attack_class('unknown_attack')
if __name__ == '__main__': unittest.main()
