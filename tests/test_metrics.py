from sentinel_ref.metrics import WorkflowMetrics, compare


def test_metric_comparison_quantifies_redesign():
    baseline = WorkflowMetrics(960, 100, 0.075, 17, 0.45)
    redesigned = WorkflowMetrics(190, 36, 0.02, 6, 1.0)
    result = compare(baseline, redesigned)

    assert result["cycle_time_reduction_pct"] == 80.21
    assert result["cost_reduction_pct"] == 64.0
    assert result["evidence_completeness_change_points"] == 55.0
