IMAGE = asia-northeast3-docker.pkg.dev/boehringer-game-260621/boehringer-repo/boehringer-game:latest
SERVICE = boehringer-game
REGION = asia-northeast1
PROJECT = boehringer-game-260621

dev:
	.venv/bin/uvicorn main:app --reload --port 8000

# 새 게임 추가:  make new-game GAME=tetris
new-game:
	.venv/bin/python scripts/new_game.py $(GAME)

# 구조·문법 검사 — 규칙 이탈 시 실패
check:
	find . -path ./.venv -prune -o -name '*.py' -print0 | xargs -0 .venv/bin/python -m py_compile
	SUPABASE_URL=https://x.supabase.co SUPABASE_KEY=x SUPABASE_SERVICE_KEY=x SECRET_KEY=t .venv/bin/python -c "import main"
	.venv/bin/python scripts/check_games.py

deploy:
	docker build --platform linux/amd64 -t $(IMAGE) .
	docker push $(IMAGE)
	gcloud run deploy $(SERVICE) --image=$(IMAGE) --region=$(REGION) --project=$(PROJECT) --allow-unauthenticated
