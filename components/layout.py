"""게임 허브 공통 레이아웃·CSS — 로비, 게임 카드, 로그인 화면."""

from fasthtml.common import *

ICONIFY_SCRIPT = Script(src="https://code.iconify.design/iconify-icon/2.1.0/iconify-icon.min.js")


def icon(name: str, size: str = "1rem"):
    """Iconify + Lucide 아이콘 — 커스텀 웹컴포넌트를 raw HTML로 출력."""
    return NotStr(
        f'<iconify-icon icon="lucide:{name}" width="{size}" height="{size}" '
        'style="vertical-align:-0.15em"></iconify-icon>'
    )


GLOBAL_CSS = Style("""
:root {
  --bg: #0f1320; --panel: #1a2032; --panel-2: #232b42;
  --accent: #5b8cff; --accent-2: #36d399; --text: #e7ecf5;
  --muted: #8a94ad; --border: #2c3450; --danger: #ff6b6b;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans KR", sans-serif;
  min-height: 100vh;
}
a { color: inherit; text-decoration: none; }
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.9rem 1.4rem; border-bottom: 1px solid var(--border);
  background: var(--panel); position: sticky; top: 0; z-index: 10;
}
.brand { display: flex; align-items: center; gap: 0.55rem; font-weight: 800; font-size: 1.15rem; letter-spacing: 0.5px; }
.brand .dot { color: var(--accent); }
.topbar-right { display: flex; align-items: center; gap: 0.8rem; }
.user-chip { color: var(--muted); font-size: 0.85rem; }
.btn {
  display: inline-flex; align-items: center; gap: 0.4rem; cursor: pointer;
  border: 1px solid var(--border); background: var(--panel-2); color: var(--text);
  padding: 0.5rem 0.9rem; border-radius: 0.6rem; font-size: 0.9rem; font-weight: 600;
}
.btn:hover { border-color: var(--accent); }
.btn-primary { background: var(--accent); border-color: var(--accent); color: #fff; }
.btn-primary:hover { filter: brightness(1.08); }
.wrap { max-width: 1100px; margin: 0 auto; padding: 1.8rem 1.4rem 4rem; }
.page-title { font-size: 1.5rem; font-weight: 800; margin: 0.2rem 0 0.3rem; }
.page-sub { color: var(--muted); margin: 0 0 1.6rem; }
.games-grid {
  display: grid; gap: 1.1rem;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}
.game-card {
  background: var(--panel); border: 1px solid var(--border); border-radius: 1rem;
  overflow: hidden; transition: transform .12s, border-color .12s; display: flex; flex-direction: column;
}
.game-card:hover { transform: translateY(-3px); border-color: var(--accent); }
.game-thumb {
  aspect-ratio: 16/10; background: linear-gradient(135deg, #2a3350, #1b2236);
  display: flex; align-items: center; justify-content: center; font-size: 2.6rem; color: var(--accent);
}
.game-thumb img { width: 100%; height: 100%; object-fit: cover; }
.game-body { padding: 0.9rem 1rem 1.1rem; }
.game-title { font-weight: 700; font-size: 1.05rem; margin: 0 0 0.25rem; }
.game-desc { color: var(--muted); font-size: 0.85rem; margin: 0 0 0.7rem; min-height: 2.2em; }
.badge {
  display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.72rem; font-weight: 700;
  background: rgba(54,211,153,0.14); color: var(--accent-2); padding: 0.2rem 0.5rem; border-radius: 0.5rem;
}
.badge.solo { background: rgba(91,140,255,0.14); color: var(--accent); }
.empty { color: var(--muted); text-align: center; padding: 3rem 1rem; }

/* 로그인 */
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 1.5rem; }
.login-card {
  width: 100%; max-width: 360px; background: var(--panel); border: 1px solid var(--border);
  border-radius: 1.1rem; padding: 2rem 1.8rem;
}
.login-logo { text-align: center; font-weight: 800; font-size: 1.4rem; margin: 0 0 1.4rem; }
.login-field { margin-bottom: 0.9rem; display: flex; flex-direction: column; gap: 0.35rem; }
.login-field label { font-size: 0.82rem; color: var(--muted); }
.form-input {
  width: 100%; padding: 0.65rem 0.8rem; border-radius: 0.6rem;
  border: 1px solid var(--border); background: var(--panel-2); color: var(--text); font-size: 0.95rem;
}
.form-input:focus { outline: none; border-color: var(--accent); }
.login-btn { width: 100%; justify-content: center; margin-top: 0.4rem; }
.login-error { color: var(--danger); font-size: 0.85rem; text-align: center; }
.text-danger { color: var(--danger); }
""")


def topbar(user: dict | None):
    """상단 바 — 브랜드 + 사용자/로그아웃."""
    right = []
    if user:
        right.append(Span(user.get("display_name") or user.get("email", ""), cls="user-chip"))
        right.append(
            Form(
                Button(icon("log-out"), " 로그아웃", type="submit", cls="btn"),
                method="post", action="/logout", hx_boost="false",
            )
        )
    return Div(
        A(Span(icon("gamepad-2"), cls="dot"), Span("BOEHRINGER", Span(".GAME", cls="dot")), href="/", cls="brand"),
        Div(*right, cls="topbar-right"),
        cls="topbar",
    )


def page(title: str, *content, user: dict | None = None):
    """공통 페이지 셸 — 상단바 + 본문."""
    return (
        Title(title),
        topbar(user),
        Div(*content, cls="wrap"),
    )
