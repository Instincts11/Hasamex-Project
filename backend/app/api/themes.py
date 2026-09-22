from fastapi import APIRouter, Depends

from app.api.deps import get_context
from app.api.schemas import (
    DifferenceOut,
    DifferencesOut,
    PositionOut,
    ThemeOut,
    ThemesOut,
    evidence_out,
)
from app.api.state import AppContext

router = APIRouter()


@router.get("/analysis/themes", response_model=ThemesOut)
def get_themes(context: AppContext = Depends(get_context)) -> ThemesOut:
    report = context.get_theme_report()
    return ThemesOut(
        themes=[
            ThemeOut(
                name=theme.name,
                summary=theme.summary,
                coverage_label=theme.coverage_label,
                single_expert=theme.single_expert,
                supporting=[evidence_out(item) for item in theme.supporting],
                conflicting=[evidence_out(item) for item in theme.conflicting],
            )
            for theme in report.themes
        ]
    )


@router.get("/analysis/differences", response_model=DifferencesOut)
def get_differences(context: AppContext = Depends(get_context)) -> DifferencesOut:
    report = context.get_theme_report()
    return DifferencesOut(
        differences=[
            DifferenceOut(
                topic=item.topic,
                summary=item.summary,
                positions=[
                    PositionOut(
                        expert=position.expert,
                        market=position.market,
                        scope=position.scope,
                        evidence=[evidence_out(citation) for citation in position.evidence],
                    )
                    for position in item.positions
                ],
            )
            for item in report.differences
        ]
    )
