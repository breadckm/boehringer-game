from dotenv import load_dotenv

load_dotenv()

import os

from fasthtml.common import *

from apps.hub import logic as hub_logic
from apps.registry import register_routes
from components.layout import GLOBAL_CSS, ICONIFY_SCRIPT, icon, page
from utils.auth import SESSION_MAX_AGE, get_current_user, redirect_to_login

_SECRET = os.environ.get("SECRET_KEY", "dev-only-secret-change-me")

# pico=False — 커스텀 CSS만 사용. secret_key → 세션 미들웨어 활성화.
app, rt = fast_app(
    hdrs=[
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        ICONIFY_SCRIPT,
        GLOBAL_CSS,
    ],
    pico=False,
    secret_key=_SECRET,
    max_age=SESSION_MAX_AGE,
    session_cookie="bg_session",
)

register_routes(app)


def _game_card(g: dict):
    """로비 게임 카드."""
    badge = (
        Span(icon("users"), " 멀티플레이어", cls="badge")
        if g.get("multiplayer")
        else Span(icon("user"), " 싱글", cls="badge solo")
    )
    thumb = (
        Img(src=f"/games/{g['id']}/{g['thumbnail']}")
        if g.get("thumbnail")
        else icon("gamepad-2", size="2.6rem")
    )
    return Div(
        A(Div(thumb, cls="game-thumb"), href=f"/play/{g['id']}"),
        Div(
            P(g["title"], cls="game-title"),
            P(g.get("desc", ""), cls="game-desc"),
            badge,
            Div(
                A("플레이", href=f"/play/{g['id']}", cls="btn btn-primary", style="flex:1; justify-content:center"),
                A(icon("trophy"), href=f"/leaderboard/{g['id']}", cls="btn", title="리더보드"),
                style="display:flex; gap:0.5rem; margin-top:0.8rem",
            ),
            cls="game-body",
        ),
        cls="game-card",
    )


@rt("/ping")
def ping():
    return "pong"


@rt("/")
def index(req, session):
    user = get_current_user(session)
    if user is None:
        return redirect_to_login(session, req=req)

    games = hub_logic.list_games()
    body = (
        Div(*[_game_card(g) for g in games], cls="games-grid")
        if games
        else P("아직 등록된 게임이 없습니다. games/ 폴더에 게임을 추가하세요.", cls="empty")
    )
    return page(
        "BOEHRINGER.GAME",
        H1("게임 로비", cls="page-title"),
        P("플레이할 게임을 선택하세요.", cls="page-sub"),
        body,
        user=user,
    )
