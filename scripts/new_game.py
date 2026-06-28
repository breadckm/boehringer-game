"""새 게임 생성 — games/_template 복사 + 게임별 테이블 자동 생성.

사용: .venv/bin/python scripts/new_game.py <game_id>   (보통 `make new-game GAME=<id>`)
"""

import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "games" / "_template"
PLACEHOLDER = "__GAME_ID__"


def main() -> int:
    from utils.db_utils import provision_game, valid_game_id

    if len(sys.argv) != 2:
        print("사용법: make new-game GAME=<game_id>")
        return 1
    game_id = sys.argv[1].strip()

    if not valid_game_id(game_id):
        print(f"잘못된 game_id: {game_id!r} (소문자로 시작, 소문자·숫자·밑줄만, 최대 41자)")
        return 1

    dest = ROOT / "games" / game_id
    if dest.exists():
        print(f"이미 존재합니다: games/{game_id}/")
        return 1

    # 1) 템플릿 복사 + 플레이스홀더 치환
    shutil.copytree(TEMPLATE, dest)
    for path in dest.rglob("*"):
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue  # 이미지 등 바이너리
            if PLACEHOLDER in text:
                path.write_text(text.replace(PLACEHOLDER, game_id), encoding="utf-8")
    print(f"✓ games/{game_id}/ 생성 (config.json·index.html·game.js·style.css)")

    # 2) 게임별 테이블 생성 (app_data_<id> · app_log_<id>)
    try:
        provision_game(game_id)
        print(f"✓ 테이블 생성: app_data_{game_id} · app_log_{game_id}")
    except Exception as e:
        print(f"! 테이블 생성 실패 — Supabase SQL 에디터에서 provision_game('{game_id}') 직접 실행 필요.")
        print(f"  사유: {e!r}")

    print("\n이제 게임을 만드세요:")
    print(f"  - games/{game_id}/game.js  ← 게임 로직")
    print(f"  - 로컬 확인: make dev → http://localhost:8000/play/{game_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
