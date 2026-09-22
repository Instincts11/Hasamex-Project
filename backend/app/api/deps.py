from fastapi import Request

from app.api.state import AppContext


def get_context(request: Request) -> AppContext:
    return request.app.state.context
