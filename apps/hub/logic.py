"""허브 로직 — games/ 디렉터리 스캔, 게임 메타데이터, 게임별 데이터/로그/점수."""

import json
from pathlib import Path

from utils import db_utils

# games/ 디렉터리 — 아들이 작업하는 정적 게임 공간
GAMES_DIR = Path(__file__).resolve().parent.parent.parent / "games"

# 밑줄로 시작하는 폴더(_template 등)는 게임 목록에서 제외
_HIDDEN_PREFIX = "_"


def list_games() -> list[dict]:
    """games/*/config.json 을 읽어 로비에 노출할 게임 목록을 만든다."""
    games: list[dict] = []
    if not GAMES_DIR.exists():
        return games
    for entry in sorted(GAMES_DIR.iterdir()):
        if entry.name.startswith(_HIDDEN_PREFIX):
            continue
        meta = _read_config(entry)
        if meta:
            games.append(meta)
    games.sort(key=lambda g: g.get("order", 100))
    return games


def get_game(game_id: str) -> dict | None:
    """단일 게임 메타데이터. game_id 형식 검증으로 경로 탈출 방지."""
    if not db_utils.valid_game_id(game_id):
        return None
    return _read_config(GAMES_DIR / game_id)


def _read_config(game_dir: Path) -> dict | None:
    """게임 폴더의 config.json + index.html 존재 여부를 확인해 메타데이터 반환."""
    if not game_dir.is_dir():
        return None
    cfg_path = game_dir / "config.json"
    index_path = game_dir / "index.html"
    if not cfg_path.exists() or not index_path.exists():
        return None
    try:
        meta = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    meta.setdefault("id", game_dir.name)
    meta.setdefault("title", game_dir.name)
    meta.setdefault("desc", "")
    meta.setdefault("multiplayer", False)
    meta.setdefault("thumbnail", "")
    return meta


def submit_score(game_id: str, user: dict, score: int) -> dict:
    """게임 점수 저장."""
    name = user.get("display_name") or user.get("email") or "익명"
    return db_utils.save_score(game_id, user["id"], name, score)


def leaderboard(game_id: str, limit: int = 10) -> list[dict]:
    """게임별 상위 점수 [{rank, name, score}]."""
    rows = db_utils.top_scores(game_id, limit)
    out = []
    for i, r in enumerate(rows, start=1):
        p = r.get("payload") or {}
        out.append({"rank": i, "name": p.get("display_name", "익명"), "score": p.get("score", 0)})
    return out
