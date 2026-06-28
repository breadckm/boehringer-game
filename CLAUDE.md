# CLAUDE.md — BOEHRINGER.GAME

## 행동 강령 (Karpathy's 4 Principles)

1. **모호하면 질문한다** — 불확실한 게 있으면 임의로 추측해서 만들지 말고 먼저 묻는다.
2. **최소한의 코드** — 요청한 것만 해결하는 가장 작은 코드를 쓴다. 쓸모없는 추상화·확장성·유연성 금지.
3. **국소적 수정** — 요청받은 부분만 건드린다. 옆 코드 리팩터·포매팅 개선 금지.
4. **검증 가능한 목표** — 구현 전에 "이걸 어떻게 확인하지?"를 먼저 정한다. 완료 기준 = `make check` 통과.

---

## 게임 철학 — 작지만 완성된 미니게임

여기서 만드는 게임은 **미니게임**이다.

- **기획 → 구현 → 버그 수정** 사이클을 빠르게 돌 수 있는 크기로 만든다.
- 방대한 시스템보다 **좁고 단단한 인터랙션**이 낫다. 규칙 5개짜리 디펜스 게임이 규칙 50개짜리 RPG보다 낫다.
- 버그가 터지면 전체를 다시 짜지 말고, **작동하는 핵심부터 확보**하고 기능을 하나씩 붙인다.
- 새 기능을 추가하기 전에 현재 게임이 **플레이 가능한 상태**인지 확인한다.
- 길을 잃으면 기획으로 돌아간다. 코드가 아니라 **게임 루프(입력 → 상태 변경 → 렌더링)**를 먼저 그린다.

---

## 명령어

```bash
make dev                     # 로컬 서버 :8000 (--reload)
make new-game GAME=<id>      # 템플릿 복사 + DB 테이블 프로비전
make check                   # 구조·문법 검사 — 완료 전 반드시 통과
make deploy                  # docker build → push → Cloud Run 배포
make scheduler-create        # /ping 웜업 Cloud Scheduler job 등록 (5분 주기)
```

`make check`는 네트워크 없이 돌아간다. 수정 후 항상 실행한다.

---

## 구조

```
main.py              # FastHTML 앱 부트스트랩, @rt("/"), @rt("/ping")
apps/hub/
  logic.py           # games/*/config.json 스캔 → 로비 목록
  routes.py          # /play/{id}, /api/score, /api/data, /leaderboard/{id}
apps/auth/routes.py  # /login, /logout, /callback
utils/auth.py        # get_current_user(), SESSION_MAX_AGE
utils/db_utils.py    # Supabase 서비스키 클라이언트, valid_game_id()
static/gamekit.js    # 브라우저 공유 라이브러리 (GameKit.*)
games/_template/     # 새 게임 시작점 (__GAME_ID__ 치환)
games/<id>/          # config.json · index.html · game.js · style.css
```

### 게임 파일 4개 규칙 (절대 변경 금지)
| 파일 | 역할 |
|---|---|
| `config.json` | title / desc / multiplayer / thumbnail / order |
| `index.html` | 빈 셸 — 허브가 `window.GAME` + supabase-js + gamekit.js 주입 |
| `game.js` | 게임 로직 전체. `GameKit.*` 호출, raw fetch/supabase 직접 호출 금지 |
| `style.css` | 게임 전용 스타일 |

### GameKit API (game.js에서 사용)
```js
GameKit.saveScore(score)          // 점수 저장
GameKit.save(key, payload)        // 게임 데이터 저장
GameKit.load(key)                 // 게임 데이터 로드
GameKit.leaderboard(n)            // 상위 n명 조회
GameKit.room(name)                // Supabase Realtime 방 (멀티플레이)
GameKit.onInput(keyMap, swipeMap) // 키보드 + 스와이프 입력
GameKit.loop(fn, fps)             // 게임 루프
GameKit.user                      // 현재 로그인 유저
```

### 데이터
- 게임별 `app_data_<id>` + `app_log_<id>` 테이블 (고정 스키마)
- 게임 고유 데이터는 `payload` JSON 컬럼에. **컬럼 추가 절대 금지.**
- DB 쓰기는 서버(서비스키)만. 브라우저에서 직접 Supabase 쓰기 금지.
- 테이블 ID는 항상 `db_utils.valid_game_id()`로 검증.

### Auth
- Supabase Auth, `bg_session` 쿠키. 모든 페이지 라우트에서 `get_current_user()` 체크.
- 비로그인 → `/login` 리다이렉트. 외부 가입 없음 (Supabase 대시보드에서만 계정 생성).

---

## 오답 노트 — 이 프로젝트에서 반복된 실수

**게임 구조**
- `make new-game GAME=<id>` 없이 `games/` 폴더를 손으로 만들지 않는다 → `make check` 실패.
- `games/_template/`의 `__GAME_ID__` 치환 없이 그대로 두지 않는다.
- 4개 파일 외에 `utils.js`, `engine.js` 등을 추가하지 않는다. 공통 로직은 `static/gamekit.js`에.

**게임 로직**
- `game.js`에서 `fetch('/api/...')` 직접 호출 금지 → `GameKit.saveScore()` 등 사용.
- `game.js`에서 `supabase.from(...)` 직접 호출 금지 → `GameKit.room()` 사용.
- `window.GAME`은 허브가 주입한다. `game.js`에서 직접 초기화하지 않는다.

**게임 설계**
- 한 번에 게임 전체를 구현하려 하지 않는다. **핵심 루프 먼저, 기능은 나중에.**
- 게임이 너무 커졌다 싶으면 기능을 뺀다. 추가보다 제거가 낫다.
- Canvas 크기를 하드코딩하지 않는다 — 모바일도 플레이하므로 반응형으로.

**백엔드**
- `app_data_<id>` 테이블에 컬럼을 추가하지 않는다 → `payload` JSON 사용.
- `apps/registry.py` 없이 새 라우터를 직접 `main.py`에 등록하지 않는다.
- Python 코드 수정 후 `make check`를 건너뛰지 않는다.

---

## 인프라 참조

| 항목 | 값 |
|---|---|
| GCP 프로젝트 | `boehringer-game-260621` |
| Cloud Run | `boehringer-game` @ `asia-northeast1` |
| Artifact Registry | `boehringer-repo` @ `asia-northeast3` |
| Cloud Run URL | `https://boehringer-game-663515997393.asia-northeast1.run.app` |
| Supabase | `.env` 참조 |

Cloud Run 환경변수: `SUPABASE_URL` · `SUPABASE_KEY` · `SUPABASE_SERVICE_KEY` · `SECRET_KEY`

---

## 코드 컨벤션
- Python: 함수 중심, FastHTML이 HTML 프래그먼트 반환. SPA 프레임워크 금지.
- 주석은 **왜**만. 한 줄. 한국어 docstring.
- `.env`, 서비스 계정 키 커밋 금지.
