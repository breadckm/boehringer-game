"""로그인·로그아웃 라우트."""

from fasthtml.common import *

from utils.auth import get_current_user, resolve_post_login_redirect
from utils.db_utils import get_supabase

router = APIRouter(prefix="")


def _page(error: str = ""):
    """로그인 전용 단독 페이지."""
    return (
        Title("로그인 — BOEHRINGER.GAME"),
        Div(
            Div(
                P("BOEHRINGER.GAME", cls="login-logo"),
                Form(
                    Div(
                        Label("이메일", fr="email"),
                        Input(id="email", name="email", type="email",
                              placeholder="user@example.com", required=True,
                              autofocus=True, cls="form-input"),
                        cls="login-field",
                    ),
                    Div(
                        Label("비밀번호", fr="password"),
                        Input(id="password", name="password", type="password",
                              placeholder="••••••••", required=True, cls="form-input"),
                        cls="login-field",
                    ),
                    P(error, cls="login-error") if error else None,
                    Button("로그인", type="submit", cls="btn btn-primary login-btn"),
                    method="post", action="/login", hx_boost="false",
                ),
                cls="login-card",
            ),
            cls="login-page",
        ),
    )


@router.get("/login")
def login_page(session, error: str = ""):
    user = get_current_user(session)
    if user:
        return RedirectResponse(resolve_post_login_redirect(session), status_code=303)
    msg = session.pop("login_error", "") if error == "1" else ""
    return _page(msg)


@router.post("/login")
def login(session, email: str = "", password: str = ""):
    if not email or not password:
        session["login_error"] = "이메일과 비밀번호를 입력하세요."
        return RedirectResponse("/login?error=1", status_code=303)
    try:
        resp = get_supabase().auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        session["access_token"] = resp.session.access_token
        session["refresh_token"] = resp.session.refresh_token
        return RedirectResponse(resolve_post_login_redirect(session), status_code=303)
    except Exception as e:
        session["login_error"] = str(e)
        return RedirectResponse("/login?error=1", status_code=303)


@router.post("/logout")
def logout(session):
    session.clear()
    return RedirectResponse("/login", status_code=303)
