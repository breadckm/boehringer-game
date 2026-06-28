"""게임 폴더 구조 검사기 — 바이브 코딩이 규칙을 벗어나면 실패시킨다.

`make check` 가 호출. 각 games/<id>/ 가 고정 레시피를 지키는지 검사한다.
ERROR가 하나라도 있으면 비정상 종료(1). WARN은 통과시키되 표시만.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES = ROOT / "games"

REQUIRED_FILES = ["config.json", "index.html", "game.js", "style.css"]
ALLOWED_ENTRIES = set(REQUIRED_FILES) | {"assets"}
CONFIG_KEYS = {"id", "title", "desc", "multiplayer", "order", "thumbnail"}
GAME_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,40}$")

# game.js가 공통 기능을 직접 짜면(=GameKit 우회) 경고
RAW_PATTERNS = [
    (re.compile(r"createClient\s*\("), "supabase 직접 생성 — GameKit.room/save 등을 쓰세요"),
    (re.compile(r"""fetch\s*\(\s*['\"]/api"""), "fetch('/api...') 직접 호출 — GameKit 메서드를 쓰세요"),
    (re.compile(r"sb_(publishable|secret)_|supabase\.co"), "URL/키 하드코딩 금지 — 서버가 주입합니다"),
]


def check_game(game_dir: Path) -> tuple[list[str], list[str]]:
    errors, warns = [], []
    name = game_dir.name

    for fn in REQUIRED_FILES:
        if not (game_dir / fn).is_file():
            errors.append(f"필수 파일 누락: {fn}")

    for entry in game_dir.iterdir():
        if entry.name not in ALLOWED_ENTRIES:
            warns.append(f"규칙 외 항목: {entry.name} (4개 파일 + assets/ 만 권장)")

    cfg_path = game_dir / "config.json"
    if cfg_path.is_file():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            missing = CONFIG_KEYS - set(cfg)
            if missing:
                warns.append(f"config.json 키 누락: {', '.join(sorted(missing))}")
            if cfg.get("id") != name:
                errors.append(f"config.json id({cfg.get('id')!r}) != 폴더명({name!r})")
            if not GAME_ID_RE.match(name):
                errors.append(f"잘못된 게임 id: {name!r} (소문자 시작, 소문자·숫자·밑줄)")
        except json.JSONDecodeError as e:
            errors.append(f"config.json 파싱 실패: {e}")

    gjs = game_dir / "game.js"
    if gjs.is_file():
        text = gjs.read_text(encoding="utf-8")
        for pat, msg in RAW_PATTERNS:
            if pat.search(text):
                warns.append(f"game.js: {msg}")

    return errors, warns


def main() -> int:
    if not GAMES.exists():
        print("games/ 디렉터리가 없습니다.")
        return 1

    total_err = 0
    for game_dir in sorted(GAMES.iterdir()):
        if not game_dir.is_dir() or game_dir.name.startswith("_"):
            continue  # _template 등 제외
        errors, warns = check_game(game_dir)
        if errors or warns:
            print(f"[{game_dir.name}]")
            for e in errors:
                print(f"  ✗ {e}")
            for w in warns:
                print(f"  ! {w}")
        else:
            print(f"[{game_dir.name}] OK")
        total_err += len(errors)

    print()
    if total_err:
        print(f"실패: 오류 {total_err}건 — 규칙 위반을 고치세요 (games/CLAUDE.md 참고).")
        return 1
    print("모든 게임 구조 OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
