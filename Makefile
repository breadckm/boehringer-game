IMAGE            = asia-northeast3-docker.pkg.dev/boehringer-game-260621/boehringer-repo/boehringer-game:latest
SERVICE          = boehringer-game
REGION           = asia-northeast1
PROJECT          = boehringer-game-260621
PROD_URL         = https://boehringer-game-663515997393.asia-northeast1.run.app
SCHEDULER_JOB    = boehringer-game-warmup

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

scheduler-create:
	gcloud scheduler jobs create http $(SCHEDULER_JOB) \
		--location=$(REGION) \
		--schedule="*/5 * * * *" \
		--uri=$(PROD_URL)/ping \
		--http-method=GET \
		--time-zone="Asia/Seoul" \
		--description="Cloud Run 웜 스타트 유지 — 5분 주기로 /ping 호출" \
		--project=$(PROJECT)

scheduler-delete:
	gcloud scheduler jobs delete $(SCHEDULER_JOB) --location=$(REGION) --project=$(PROJECT)

scheduler-status:
	gcloud scheduler jobs describe $(SCHEDULER_JOB) --location=$(REGION) --project=$(PROJECT)
