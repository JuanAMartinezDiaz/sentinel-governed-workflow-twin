from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_decision_xray_2_entrypoint_is_wired():
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    assert 'id="xrayCanvas"' in html
    assert 'src="xray2.js"' in html
    assert 'href="xray2.css"' in html
    assert html.count('data-scenario=') == 5
    assert 'DECISION X-RAY 2.0' in html
