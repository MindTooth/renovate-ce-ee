"""Render regression tests: python -m unittest discover -s helm-charts/tests.

Requires Helm (as used by chart-testing) and PyYAML (a chart-testing dependency).
"""
import subprocess
import unittest
from pathlib import Path

import yaml

CHARTS = Path(__file__).resolve().parents[1]


def render(edition, values=None):
    result = subprocess.run(
        ['helm', 'template', 'test', str(CHARTS / f'mend-renovate-{edition}'),
         '--namespace', 'renovate', '-f', '-'],
        input=yaml.safe_dump(values or {}), text=True, capture_output=True, check=True,
    )
    return [doc for doc in yaml.safe_load_all(result.stdout) if doc]


def routes(documents):
    return [doc for doc in documents if doc['kind'] == 'Route']


class RoutesTest(unittest.TestCase):
    def test_defaults(self):
        for edition in ('ce', 'ee'):
            with self.subTest(edition=edition):
                self.assertEqual(routes(render(edition)), [])

    def test_routes(self):
        for edition, key, backend in (
            ('ce', 'route', ''), ('ee', 'route', '-svc-server'),
            ('ee', 'routeWeb', '-svc-web'),
        ):
            with self.subTest(edition=edition, key=key):
                values = {key: {'enabled': True}, 'renovateWeb': {'enabled': True},
                          'fullnameOverride': 'custom-renovate'}
                documents = render(edition, values)
                route, = routes(documents)
                self.assertEqual(route['apiVersion'], 'route.openshift.io/v1')
                self.assertEqual(route['metadata']['namespace'], 'renovate')
                self.assertEqual(route['metadata']['labels']['app.kubernetes.io/instance'], 'test')
                self.assertNotIn('host', route['spec'])
                self.assertNotIn('annotations', route['metadata'])
                self.assertEqual(route['spec']['port']['targetPort'], 'http')
                self.assertEqual(route['spec']['tls'], {
                    'termination': 'edge', 'insecureEdgeTerminationPolicy': 'Redirect'})
                service = next(doc for doc in documents if doc['kind'] == 'Service'
                               and doc['metadata']['name'].endswith(backend)
                               and (backend or doc['metadata']['name'] == route['metadata']['name']))
                self.assertEqual(service['metadata']['name'], 'custom-renovate' + backend)
                self.assertEqual(route['spec']['to'], {'kind': 'Service', 'name': service['metadata']['name']})
                self.assertIn('http', [port['name'] for port in service['spec']['ports']])
                values[key].update(host='renovate.example.com', annotations={'example.com/key': 'value'}, targetPort='https')
                custom, = routes(render(edition, values))
                self.assertEqual(custom['spec']['host'], 'renovate.example.com')
                self.assertEqual(custom['metadata']['annotations'], {'example.com/key': 'value'})
                self.assertEqual(custom['spec']['port']['targetPort'], 'https')
                values[key]['tls'] = None
                plain, = routes(render(edition, values))
                self.assertNotIn('tls', plain['spec'])
                values[key]['tls'] = {'termination': 'passthrough'}
                with self.assertRaises(subprocess.CalledProcessError):
                    render(edition, values)

    def test_web_guard(self):
        for web, route in ((False, True), (True, False), (False, False)):
            self.assertEqual(routes(render('ee', {
                'renovateWeb': {'enabled': web}, 'routeWeb': {'enabled': route}})), [])

    def test_independence(self):
        documents = render('ee', {'route': {'enabled': True}})
        self.assertEqual(len(routes(documents)), 1)
        self.assertFalse(any(doc['kind'] == 'Service' and doc['metadata']['name'].endswith('-svc-web') for doc in documents))
        documents = render('ee', {'renovateWeb': {'enabled': True},
            'route': {'enabled': True, 'host': 'api.example.com'},
            'routeWeb': {'enabled': True, 'host': 'web.example.com'}})
        self.assertEqual({r['spec']['host'] for r in routes(documents)}, {'api.example.com', 'web.example.com'})
        self.assertEqual(len({r['metadata']['name'] for r in routes(documents)}), 2)

    def test_ingress_unchanged(self):
        for edition in ('ce', 'ee'):
            values = {'ingress': {'enabled': True}}
            before = render(edition, values)
            values.update(route={'enabled': True}, routeWeb={'enabled': True}, renovateWeb={'enabled': True})
            after = render(edition, values)
            for kind in ('Ingress', 'Service'):
                original = [d for d in before if d['kind'] == kind]
                self.assertTrue(original)
                for document in original:
                    self.assertIn(document, after)
