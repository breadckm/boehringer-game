"""인증·세션·권한 헬퍼."""

from utils.db_utils import ACCESS_ADMIN, get_profile, get_supabase

SESSION_MAX_AGE = 60 * 60 * 24 * 365  # 1년 — Supabase refresh token으로 자동 갱신
LOGIN_NEXT_KEY = "login_next"


def _fetch_auth_user(token: str):
    try:
        return get_supabase().auth.get_user(token)
    except Exception:
        return None


def _refresh_session_tokens(session: dict) -> bool:
    """access_token 만료 시 refresh_token으로 갱신. 성공 시 세션 dict를 갱신."""
    refresh = session.get("refresh_token")
    if not refresh:
        return False
    try:
        resp = get_supabase().auth.refresh_session(refresh)
        if not resp or not resp.session:
            return False
        session["access_token"] = resp.session.access_token
        session["refresh_token"] = resp.session.refresh_token
        return True
    except Exception:
        return False


def _profile_from_auth_user(user) -> dict:
    uid = str(user.id)
    profile = get_profile(uid) or {}
    profile.setdefault("id", uid)
    profile.setdefault("email", user.email)
    profile.setdefault("display_name", user.email)
    profile.setdefault("access_level", 10)
    return profile


def get_current_user(session: dict) -> dict | None:
    """세션 dict에서 현재 사용자 프로필 반환. 미인증·토큰 만료 시 None.

    access_token 만료 시 refresh_token으로 자동 갱신한다.
    FastHTML에서 session은 route 파라미터로 주입된다.
    """
    token = session.get("access_token")
    if not token:
        return None

    user_resp = _fetch_auth_user(token)
    if not user_resp or not user_resp.user:
        if not _refresh_session_tokens(session):
            return None
        user_resp = _fetch_auth_user(session.get("access_token", ""))
        if not user_resp or not user_resp.user:
            return None

    return _profile_from_auth_user(user_resp.user)


def is_admin(profile: dict | None) -> bool:
    """관리자(99 이상) 여부."""
    return bool(profile) and profile.get("access_level", 0) >= ACCESS_ADMIN


def _safe_next_path(path: str) -> str | None:
    if not path or not path.startswith("/") or path.startswith("//"):
        return None
    if path.startswith("/login"):
        return None
    return path


def redirect_to_login(session: dict, *, req=None, path: str | None = None):
    """로그인 페이지로 보내기 전, 돌아올 경로를 세션에 저장한다."""
    from starlette.responses import RedirectResponse

    target = path
    if target is None and req is not None:
        target = req.url.path
        if req.url.query:
            target = f"{target}?{req.url.query}"
    safe = _safe_next_path(target) if target else None
    if safe:
        session[LOGIN_NEXT_KEY] = safe
    return RedirectResponse("/login", status_code=303)


def pop_login_next(session: dict) -> str | None:
    return _safe_next_path(session.pop(LOGIN_NEXT_KEY, "") or "")


def resolve_post_login_redirect(session: dict) -> str:
    """로그인 성공 후 이동할 URL. 저장된 next가 있으면 그곳으로, 없으면 허브."""
    next_url = pop_login_next(session)
    return next_url or "/"
