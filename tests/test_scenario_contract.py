from html.parser import HTMLParser
import json
from pathlib import Path

import pytest

from api.demo import run_scenario
from api.scenarios import SCENARIOS
from scripts.sync_demo_scenarios import (
    END, START, browser_scenarios, check_pr_body, generated_files, scenario_summary,
)

ROOT = Path(__file__).parents[1]


class ScenarioButtons(HTMLParser):
    def __init__(self):
        super().__init__()
        self.keys = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-scenario' in attrs:
            assert tag == 'button'
            self.keys.append(attrs['data-scenario'])


def test_generated_docs_buttons_and_offline_traces_are_current():
    for name, expected in generated_files().items():
        assert (ROOT / name).read_text() == expected, f'Regenerate {name}'


def test_every_api_scenario_has_exactly_one_visual_choice():
    parser = ScenarioButtons()
    parser.feed((ROOT / 'docs/index.html').read_text())
    browser = browser_scenarios()
    assert len(parser.keys) == len(set(parser.keys)) == len(SCENARIOS)
    assert set(parser.keys) == set(browser)
    assert {s['apiScenario'] for s in browser.values()} == set(SCENARIOS)


@pytest.mark.parametrize('scenario', SCENARIOS)
def test_generated_browser_contract_matches_engine(scenario):
    spec = SCENARIOS[scenario]
    visual = browser_scenarios()[spec['visual']['key']]
    result = run_scenario(scenario)
    assert visual['disp'] == result['decision']
    assert f"confidence {spec['confidence']:.2f}" in visual['trace']
    assert spec['tool_name'] in visual['trace']
    assert 'ILLUSTRATIVE' in visual['trace']
    if spec['human_approved']:
        assert 'simulated' in visual['summary'].lower()
        assert 'SIMULATED APPROVAL' in visual['label']
        assert result['approval_note'] in visual['trace']


def test_generated_assets_are_stable_and_do_not_publish_transient_evidence():
    first = browser_scenarios()
    assert first == browser_scenarios()
    text = json.dumps(first)
    assert 'decision_id' not in text
    assert 'recorded_at' not in text
    assert 'signature' not in text


def test_pr_description_contract_accepts_current_summary():
    check_pr_body('## Summary\n\n' + scenario_summary() + '\n\n## Verification\n')


@pytest.mark.parametrize('body', [
    'Restrict requests to five fixed synthetic scenarios.',
    scenario_summary().replace('**6 fixed synthetic scenarios**', '**5 fixed synthetic scenarios**'),
    scenario_summary().replace('`unapproved-tool`', '`something-else`'),
    scenario_summary() + '\n' + scenario_summary(),
    START + '\nUnverified summary\n' + END,
])
def test_pr_description_contract_rejects_drift(body):
    with pytest.raises(ValueError, match='missing or stale'):
        check_pr_body(body)
