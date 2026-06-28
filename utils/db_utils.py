"""데이터베이스 공통 접근 — Supabase 클라이언트·프로필·게임별 테이블 접근.

게임 데이터는 게임마다 별도 테이블에 저장한다(컬럼 스키마는 전 게임 동일):
  app_data_<게임id> : id · user_id · data_type · reference_id · payload · created_at
  app_log_<게임id>  : id · user_id · event · payload · created_at
테이블명을 코드에서 조합하므로 game_id는 반드시 valid_game_id로 검증한다.
"""

import os
import re
import time
from typing import Callable, TypeVar

import httpx
from supabase import Client, ClientOptions, create_client

ACCESS_NORMAL = 10
ACCESS_ADMIN = 99  # 이상이면 제한 없이 전체 접근

# 게임 ID 형식 — 테이블명(app_data_<id>)에 그대로 들어가므로 엄격히 제한
_GAME_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,40}$")
DATA_SELECT = "id, user_id, data_type, reference_id, payload, created_at"

T = TypeVar("T")
_SUPABASE_TRANSIENT = (
    httpx.RemoteProtocolError,
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.PoolTimeout,
    httpx.NetworkError,
)

_supabase: Client | None = None
_supabase_admin: Client | None = None


def valid_game_id(game_id: str) -> bool:
    """game_id가 테이블명에 안전한 형식인지 검증(소문자/숫자/밑줄)."""
    return bool(game_id) and bool(_GAME_ID_RE.match(game_id))


def _data_table_name(game_id: str) -> str:
    if not valid_game_id(game_id):
        raise ValueError(f"invalid game_id: {game_id!r}")
    return f"app_data_{game_id}"


def _log_table_name(game_id: str) -> str:
    if not valid_game_id(game_id):
        raise ValueError(f"invalid game_id: {game_id!r}")
    return f"app_log_{game_id}"


def _reset_supabase_admin() -> None:
    global _supabase_admin
    _supabase_admin = None


def supabase_execute(fn: Callable[[], T], *, retries: int = 3) -> T:
    """Supabase .execute() 호출 — HTTP/2 끊김 등 일시 오류 시 재시도."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            return fn()
        except _SUPABASE_TRANSIENT as exc:
            last = exc
            _reset_supabase_admin()
            if attempt < retries - 1:
                time.sleep(0.5 * (2 ** attempt))
    raise last  # type: ignore[misc]


def get_supabase() -> Client:
    """Publishable key — 일반 API (RLS 적용)."""
    global _supabase
    if _supabase is None:
        opts = ClientOptions(auto_refresh_token=False, persist_session=False)
        _supabase = create_client(
            os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"], options=opts
        )
    return _supabase


def get_supabase_admin() -> Client:
    """Secret key — 서버 관리·RLS 우회 작업."""
    global _supabase_admin
    if _supabase_admin is None:
        _supabase_admin = create_client(
            os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"]
        )
    return _supabase_admin


def get_profile(user_id: str) -> dict | None:
    """user_profiles 단건 조회."""
    def _q():
        return (
            get_supabase_admin()
            .table("user_profiles")
            .select("id, display_name, user_category, access_level, allowed_apps")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

    return (supabase_execute(_q).data or [None])[0]


def provision_game(game_id: str) -> None:
    """게임별 테이블(app_data_<id>·app_log_<id>)을 생성한다(provision_game RPC)."""
    if not valid_game_id(game_id):
        raise ValueError(f"invalid game_id: {game_id!r}")
    get_supabase_admin().rpc("provision_game", {"p_game_id": game_id}).execute()


def save_data(
    game_id: str,
    user_id: str,
    payload: dict,
    *,
    data_type: str = "default",
    reference_id: str | None = None,
) -> dict:
    """게임 데이터 1건을 app_data_<id>에 저장."""
    row = {"user_id": user_id, "data_type": data_type, "reference_id": reference_id, "payload": payload}

    def _q():
        return get_supabase_admin().table(_data_table_name(game_id)).insert(row).execute()

    res = supabase_execute(_q)
    return res.data[0] if res.data else row


def load_data(game_id: str, user_id: str, data_type: str = "default", limit: int = 50) -> list[dict]:
    """사용자별 게임 데이터 최신순 목록."""
    def _q():
        return (
            get_supabase_admin()
            .table(_data_table_name(game_id))
            .select(DATA_SELECT)
            .eq("user_id", user_id)
            .eq("data_type", data_type)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

    return supabase_execute(_q).data or []


def save_score(game_id: str, user_id: str, display_name: str, score: int) -> dict:
    """게임 점수 1건 저장(data_type='score')."""
    return save_data(
        game_id, user_id,
        {"display_name": display_name, "score": int(score)},
        data_type="score",
    )


def top_scores(game_id: str, limit: int = 10) -> list[dict]:
    """게임별 최고 점수 목록(payload.score 내림차순)."""
    def _q():
        return (
            get_supabase_admin()
            .table(_data_table_name(game_id))
            .select(DATA_SELECT)
            .eq("data_type", "score")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )

    rows = supabase_execute(_q).data or []
    rows.sort(key=lambda r: (r.get("payload") or {}).get("score", 0), reverse=True)
    return rows[:limit]


def write_log(game_id: str, user_id: str | None, event: str, payload: dict | None = None) -> None:
    """게임 로그 1건을 app_log_<id>에 기록."""
    row = {"user_id": user_id, "event": event, "payload": payload or {}}

    def _q():
        return get_supabase_admin().table(_log_table_name(game_id)).insert(row).execute()

    supabase_execute(_q)
