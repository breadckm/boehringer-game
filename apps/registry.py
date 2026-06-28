"""라우터 등록 — 신규 게임/기능은 여기에 한 줄씩 추가한다."""


def register_routes(app) -> None:
    """등록된 라우터를 FastHTML 앱에 연결."""
    from apps.auth.routes import router as auth_router
    from apps.hub.routes import router as hub_router

    for router in (auth_router, hub_router):
        router.to_app(app)
