from app.llm.client import MockLLMProvider
from app.services.evidence_store import EvidenceStore
from app.services.theme_service import analyze_themes

GROWTH_CLAIMS = {
    "claims": [
        {
            "topic": "procedure-volume growth",
            "claim": "15 to 20 percent more procedures annually in some stronger centres.",
            "scope": "France, stronger centres",
            "evidence_ids": ["ev_france_006"],
        },
        {
            "topic": "procedure-volume growth",
            "claim": "High single digits or low double digits rather than 20 percent across the whole market.",
            "scope": "Germany, whole market",
            "evidence_ids": ["ev_germany_006"],
        },
        {
            "topic": "procedure-volume growth",
            "claim": "Procedure growth above 15 percent annually in some areas.",
            "scope": "United Kingdom, some areas",
            "evidence_ids": ["ev_united_kingdom_005"],
        },
        {
            "topic": "purchase economics",
            "claim": "The economic case decides approval.",
            "scope": "Germany",
            "evidence_ids": ["ev_germany_003"],
        },
        {
            "topic": "purchase economics",
            "claim": "Economics and clinical strategy are balanced.",
            "scope": "United Kingdom",
            "evidence_ids": ["ev_united_kingdom_004"],
        },
    ]
}

GROWTH_THEMES = {
    "themes": [
        {
            "name": "Adoption growth expectations",
            "summary": "Experts expect continued growth, but rates and scope differ by market.",
            "supporting_evidence_ids": [
                "ev_france_006",
                "ev_germany_006",
                "ev_united_kingdom_005",
            ],
            "conflicting_evidence_ids": [],
        },
        {
            "name": "Role of economics in purchasing",
            "summary": "Germany treats the economic case as decisive; the UK balances economics and clinical strategy.",
            "supporting_evidence_ids": ["ev_germany_003"],
            "conflicting_evidence_ids": ["ev_united_kingdom_004"],
        },
        {
            "name": "UK training capacity",
            "summary": "Training capacity is as important as funding.",
            "supporting_evidence_ids": ["ev_united_kingdom_002"],
            "conflicting_evidence_ids": [],
        },
    ],
    "differences": [
        {
            "topic": "Growth rate and scope",
            "summary": "Forecasts share a topic but not a single market-wide rate.",
            "evidence_ids": [
                "ev_france_006",
                "ev_germany_006",
                "ev_united_kingdom_005",
            ],
        }
    ],
}


def test_theme_analysis_preserves_growth_scope(evidence_store: EvidenceStore) -> None:
    provider = MockLLMProvider([GROWTH_CLAIMS, GROWTH_THEMES])
    report = analyze_themes(evidence_store, provider)

    scopes = {claim.scope for claim in report.claims if claim.topic == "procedure-volume growth"}
    assert "France, stronger centres" in scopes
    assert "Germany, whole market" in scopes
    assert "United Kingdom, some areas" in scopes
    assert all(
        theme.summary.lower() != "the market will grow 15–20%"
        and theme.summary.lower() != "the market will grow 15-20%"
        for theme in report.themes
    )

    growth = next(item for item in report.differences if item.topic == "Growth rate and scope")
    assert {position.market for position in growth.positions} == {
        "France",
        "Germany",
        "United Kingdom",
    }
    france = next(item for item in growth.positions if item.market == "France")
    assert france.scope == "France, stronger centres"
    assert "15 to 20 percent" in france.evidence[0].quote.lower()
    assert "stronger centres" in france.evidence[0].quote.lower()


def test_conflicting_evidence_is_preserved(evidence_store: EvidenceStore) -> None:
    provider = MockLLMProvider([GROWTH_CLAIMS, GROWTH_THEMES])
    report = analyze_themes(evidence_store, provider)
    economics = next(item for item in report.themes if "economics" in item.name.lower())
    assert economics.conflicting
    assert "balanced" in economics.conflicting[0].quote.lower()
    assert economics.conflicting[0].market == "United Kingdom"


def test_single_expert_theme_is_labeled(evidence_store: EvidenceStore) -> None:
    provider = MockLLMProvider([GROWTH_CLAIMS, GROWTH_THEMES])
    report = analyze_themes(evidence_store, provider)
    training = next(item for item in report.themes if "training" in item.name.lower())
    assert training.single_expert is True
    assert training.coverage_label == "Single-expert evidence (United Kingdom)"


def test_unknown_claim_ids_are_dropped(evidence_store: EvidenceStore) -> None:
    provider = MockLLMProvider(
        [
            {
                "claims": [
                    {
                        "topic": "price",
                        "claim": "Systems cost two million.",
                        "scope": None,
                        "evidence_ids": ["ev_invented"],
                    },
                    {
                        "topic": "barriers",
                        "claim": "Capital approval is the biggest issue.",
                        "scope": "France",
                        "evidence_ids": ["ev_france_002"],
                    },
                ]
            },
            {"themes": [], "differences": []},
        ]
    )
    report = analyze_themes(evidence_store, provider)
    assert [claim.topic for claim in report.claims] == ["barriers"]
    assert report.themes == []
