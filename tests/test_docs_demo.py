from pathlib import Path

ROOT = Path(__file__).parents[1]

def test_decision_xray_2_entrypoint_is_wired():
    html = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    assert 'id="xrayCanvas"' in html
    assert 'src="xray2.js"' in html
    assert 'href="xray2.css"' in html
    assert html.count('data-scenario=') == 5
    assert 'DECISION X-RAY 2.0' in html


def test_xray_canvas_is_opaque_and_has_no_recursive_screenshot_background():
    js = (ROOT / "docs" / "xray2.js").read_text(encoding="utf-8")
    css = (ROOT / "docs" / "xray2.css").read_text(encoding="utf-8")
    assert 'alpha:false' in js
    assert 'setClearColor(0x04101a,1)' in js
    assert 'decision-xray2-live.png' not in css
