"""허브 라우트 — 게임 셸 서빙, 정적 에셋, 데이터/점수/로그 API, 리더보드."""

import json
import os

from fasthtml.common import *
from starlette.responses import FileResponse, HTMLResponse, JSONResponse

from components.layout import icon, page
from utils import db_utils
from utils.auth import get_current_user, redirect_to_login
from . import logic
from .logic import GAMES_DIR

router = APIRouter(prefix="")


def _inject_game_config(html: str, game_id: str, user: dict) -> str:
    """게임 index.html에 브라우저용 Supabase 설정·유저 정보를 주입한다.

    SUPABASE_KEY는 publishable(anon) 키로 브라우저 노출이 안전하다.
    실제 헬퍼(saveScore·room·load 등)는 /static/gamekit.js 가 window.GAME 위에 얹는다.
    """
    cfg = {
        "id": game_id,
        "supabaseUrl": os.environ.get("SUPABASE_URL", ""),
        "supabaseAnonKey": os.environ.get("SUPABASE_KEY", ""),
        "user": {"id": user["id"], "name": user.get("display_name") or user.get("email", "")},
    }
    snippet = (
        '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>\n'
        f"<script>window.GAME = {json.dumps(cfg, ensure_ascii=False)};</script>\n"
        '<script src="/static/gamekit.js"></script>'
    )
    if "</head>" in html:
        return html.replace("</head>", snippet + "\n</head>", 1)
    return snippet + html


@router.get("/play/{game_id}")
def play(req, session, game_id: str):
    """게임 화면(셸) — 인증된 사용자에게 설정 주입된 index.html 반환."""
    user = get_current_user(session)
    if not user:
        return redirect_to_login(session, req=req)
    if not logic.get_game(game_id):
        return HTMLResponse("<h1>게임을 찾을 수 없습니다.</h1>", status_code=404)
    html = (GAMES_DIR / game_id / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(_inject_game_config(html, game_id, user))


@router.get("/games/{game_id}/{fname:path}")
def game_asset(session, game_id: str, fname: str):
    """게임 정적 에셋(game.js, style.css, 이미지 등) 서빙."""
    if not get_current_user(session):
        return HTMLResponse("Unauthorized", status_code=401)
    if not db_utils.valid_game_id(game_id):
        return HTMLResponse("Forbidden", status_code=403)
    base = (GAMES_DIR / game_id).resolve()
    target = (base / fname).resolve()
    # 경로 탈출 차단 — games/<id>/ 밖의 파일은 접근 불가
    if base != target and base not in target.parents:
        return HTMLResponse("Forbidden", status_code=403)
    if not target.is_file():
        return HTMLResponse("Not found", status_code=404)
    return FileResponse(target)


@router.get("/leaderboard/{game_id}")
def leaderboard_page(req, session, game_id: str):
    """게임별 리더보드 페이지."""
    user = get_current_user(session)
    if not user:
        return redirect_to_login(session, req=req)
    meta = logic.get_game(game_id)
    if not meta:
        return HTMLResponse("<h1>게임을 찾을 수 없습니다.</h1>", status_code=404)
    rows = logic.leaderboard(game_id, limit=20)
    table = (
        Table(
            Thead(Tr(Th("#"), Th("플레이어"), Th("점수"))),
            Tbody(*[Tr(Td(r["rank"]), Td(r["name"]), Td(str(r["score"]))) for r in rows]),
            style="width:100%; border-collapse:collapse",
        )
        if rows
        else P("아직 기록이 없습니다.", cls="empty")
    )
    return page(
        f"{meta['title']} 리더보드",
        A(icon("arrow-left"), " 로비로", href="/", cls="btn", style="margin-bottom:1rem"),
        H1(meta["title"], cls="page-title"),
        P("최고 점수 TOP 20", cls="page-sub"),
        table,
        user=user,
    )


async def _authed_json_body(req, session):
    """공통 — 인증 + JSON 바디 파싱. (user, body) 또는 (None, JSONResponse) 반환."""
    user = get_current_user(session)
    if not user:
        return None, JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
    try:
        body = await req.json()
    except Exception:
        return None, JSONResponse({"ok": False, "error": "bad json"}, status_code=400)
    return user, body


@router.post("/api/score")
async def api_score(req, session):
    """게임에서 점수 저장 요청."""
    user, body = await _authed_json_body(req, session)
    if user is None:
        return body
    game_id = body.get("game_id", "")
    if not logic.get_game(game_id):
        return JSONResponse({"ok": False, "error": "unknown game"}, status_code=400)
    try:
        score = int(body.get("score", 0))
    except (TypeError, ValueError):
        return JSONResponse({"ok": False, "error": "invalid score"}, status_code=400)
    logic.submit_score(game_id, user, score)
    return JSONResponse({"ok": True, "score": score})


@router.post("/api/data")
async def api_save_data(req, session):
    """게임 세이브/상태 데이터 저장."""
    user, body = await _authed_json_body(req, session)
    if user is None:
        return body
    game_id = body.get("game_id", "")
    if not logic.get_game(game_id):
        return JSONResponse({"ok": False, "error": "unknown game"}, status_code=400)
    row = db_utils.save_data(
        game_id, user["id"], body.get("payload") or {},
        data_type=body.get("data_type", "default"),
        reference_id=body.get("reference_id"),
    )
    return JSONResponse({"ok": True, "id": row.get("id")})


@router.get("/api/data/{game_id}")
def api_load_data(session, game_id: str, data_type: str = "default"):
    """본인의 게임 데이터 목록 조회."""
    user = get_current_user(session)
    if not user:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if not logic.get_game(game_id):
        return JSONResponse({"error": "unknown game"}, status_code=400)
    return JSONResponse({"rows": db_utils.load_data(game_id, user["id"], data_type)})


@router.post("/api/log")
async def api_log(req, session):
    """게임 로그 기록."""
    user, body = await _authed_json_body(req, session)
    if user is None:
        return body
    game_id = body.get("game_id", "")
    if not logic.get_game(game_id):
        return JSONResponse({"ok": False, "error": "unknown game"}, status_code=400)
    db_utils.write_log(game_id, user["id"], str(body.get("event", "")), body.get("payload") or {})
    return JSONResponse({"ok": True})


@router.get("/api/leaderboard/{game_id}")
def api_leaderboard(session, game_id: str):
    """게임 내부에서 부를 리더보드 JSON."""
    if not get_current_user(session):
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return JSONResponse({"rows": logic.leaderboard(game_id, limit=10)})
