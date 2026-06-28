# games/ — 게임 제작 규칙 (절대 어기지 말 것)

이 폴더 안에서 게임을 만들 때는 **아래 고정 레시피를 그대로** 따른다. 새로운 구조를
발명하지 않는다. 일관성이 최우선이다 — 모든 게임은 똑같은 모양이어야 한다.

## 시작 방법 (항상 동일)
- 새 게임은 **반드시** `make new-game GAME=<id>` 로 시작한다 (`games/_template/`를 복사 + DB 테이블 자동 생성).
- 맨손으로 폴더를 만들지 않는다. `<id>` 는 소문자로 시작, 소문자·숫자·밑줄만.

## 폴더 구조 (이 4개 파일이 전부)
```
games/<id>/
├── config.json   # 메타데이터 (id·title·desc·multiplayer·order·thumbnail)
├── index.html    # 화면 쉘
├── game.js       # 게임 로직 (여기만 주로 편집)
└── style.css     # 스타일
└── assets/       # (선택) 이미지·사운드만
```
- 파일을 더 늘리지 않는다. 로직은 `game.js` 하나에 둔다.
- 빌드 도구·프레임워크·npm·번들러 금지. **순수 HTML/CSS/Canvas/바닐라 JS만.**

## 공통 기능은 GameKit 으로만 (직접 짜지 말 것)
`window.GameKit` 이 공통 기능을 모두 제공한다. **`fetch()` 나 `supabase` 를 직접 호출하지 않는다.
URL·키를 하드코딩하지 않는다.**
- 점수: `GameKit.saveScore(점수)` / `GameKit.leaderboard()`
- 세이브·불러오기: `GameKit.save(type, data)` / `GameKit.load(type)`
- 로그: `GameKit.log(event, data)`
- 멀티플레이어: `GameKit.room(name).on(...).send(...).onPlayers(...).join()`
- 입력: `GameKit.onInput({up,down,left,right})`
- 루프: `GameKit.loop(fn, fps)` · 색상: `GameKit.colorFor(seed)` · 유저: `GameKit.user`
- 공통 기능이 부족하면 **게임이 아니라 `static/gamekit.js` 를 한 번 확장**한다.

## 데이터 규칙
- 게임 데이터는 `make new-game` 이 만든 `app_data_<id>` · `app_log_<id>` 에 자동 저장된다.
- 게임마다 다른 값은 **`payload`(JSON) 안에** 넣는다. **컬럼·테이블을 손으로 추가하지 않는다.**

## 경계
- `games/<id>/` 밖은 건드리지 않는다 (`main.py`·`apps/`·`utils/`·다른 게임 금지).
- 에셋 경로는 절대경로: `/games/<id>/...`
- 끝나면 `make check` 가 통과해야 한다.
