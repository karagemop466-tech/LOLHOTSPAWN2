#!/usr/bin/env python3
"""Regression tests: source reachability is not official result verification."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from provenance import annotate_matches, source_kind
from update_picks import build_league_breakdown


class ProvenanceTests(unittest.TestCase):
    def test_source_identity_is_host_based(self):
        for url, kind in [
            ('https://www.hotspawn.com/matches/a', 'fixture_provider'),
            ('https://lol.fandom.com/wiki/A', 'community_reference'),
            ('https://liquipedia.net/leagueoflegends/A', 'community_reference'),
            ('https://www.pinnacle.com/en/esports', 'market_publisher'),
            ('https://www.unibet.com.au/betting', 'market_publisher'),
            ('https://lol.fandom.com.evil.test/wiki/A', 'unclassified_reference'),
            ('https://evil.test/?url=https://www.hotspawn.com', 'unclassified_reference'),
            ('', 'unclassified_reference'),
        ]:
            with self.subTest(url=url): self.assertEqual(source_kind(url), kind)

    def test_never_infers_official_verification(self):
        for method, market, kind in [('MODEL_ELO', None, 'model_estimate'),
                                      ('MODEL_STANDINGS', None, 'model_estimate'),
                                      ('MARKET_SINGLE', {'source_count': 1}, 'market_derived'),
                                      ('UNRESOLVED', None, 'unavailable')]:
            row = {'method': method, 'market': market, 'prob_team1': .61,
                   'sources': [{'url': 'https://lol.fandom.com/wiki/A', 'name': 'Official!'}]}
            annotate_matches([row])
            self.assertEqual(row['verification']['probability_kind'], kind)
            self.assertIsNone(row['verification']['official_results_confirmed'])
            self.assertIsNone(row['verification']['official_results_source'])
            self.assertEqual(row['prob_team1'], .61)  # annotation cannot change the model
            self.assertEqual(row['sources'][0]['source_kind'], 'community_reference')

    def test_absent_line_is_not_universal_nonexistence(self):
        for method in ('MODEL_ELO', 'MODEL_LEAGUE_PRIOR', 'UNRESOLVED'):
            row = {'tournament': 'Test League', 'method': method, 'market': None}
            lim = build_league_breakdown([row])[0]['limitation']
            self.assertIn('configured adapters', lim)
            self.assertNotIn('No bookmaker prices', lim)

    def test_css_block_balance(self):
        import re
        root = Path(__file__).resolve().parents[1]
        css = re.sub(r'/\*.*?\*/', '', (root/'docs/assets/style.css').read_text(), flags=re.S)
        self.assertEqual(css.count('{'), css.count('}'), 'integration must not nest the phone rules accidentally')

    def test_policy_ui_has_no_false_authority(self):
        root = Path(__file__).resolve().parents[1]
        for path in (root/'docs').glob('*.html'):
            self.assertNotIn('official split standings', path.read_text())
        app = (root/'docs/assets/app.js').read_text()
        self.assertNotIn('fixtures have a verified pick', app)
        self.assertNotIn('verified link${', app)
        self.assertIn('NO PICK · insufficient evidence', app)


if __name__ == '__main__': unittest.main()
