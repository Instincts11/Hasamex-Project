from eval.run_eval import run_eval


def test_golden_eval_is_grounded_and_quote_accurate() -> None:
    report = run_eval()
    by_id = {row["id"]: row for row in report["cases"]}

    assert by_id["price-unsupported"]["groundedness"] == 1.0
    assert by_id["price-unsupported"]["cited_ids"] == []
    assert report["summary"]["quote_accuracy"] == 1.0
    assert report["summary"]["groundedness"] == 1.0
    assert by_id["purchase-timelines"]["evidence_coverage"] == 1.0
    assert by_id["economics-not-alone"]["completeness"] > 0
