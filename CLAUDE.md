# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## What this is

BOEHRINGER.GAME is a multiplayer game hub. A single FastHTML server (the "hub") authenticates
users and serves a lobby of browser games. Each game lives in `games/<name>/` as plain static
files (HTML/CSS/JS) and talks to **Supabase Realtime directly from the browser** for live
multiplayer sync — the Python backend never relays gameplay traffic.

This mirrors the `~/Projects/chat_shire` stack (FastHTML + HTMX + Supabase + Cloud Run) but adds a
browser-side realtime layer and isolates game content as static files.

## Division of work

- **Backend / hub (Python, FastHTML):** `apps/`, `utils/`, `components/`, `main.py`. Auth gating,
  lobby dashboard, game-shell serving, score API, leaderboards.
- **Games (browser only):** `games/<name>/`. Pure HTML/Canvas/JS. No Python knowledge needed.
  The hub injects `window.GAME` (Supabase client, user, `saveScore()`) into each game's page.

## Commands

```bash
make dev               # local server on :8000 with --reload
make new-game GAME=<id># scaffold a game from games/_template + provision its DB tables
make check             # correctness gate: py_compile + import main + game-structure validator
make deploy            # docker build --platform linux/amd64 → push → gcloud run deploy
```

No test suite. `make check` is the gate (no network needed) — it must pass before reporting done.
It runs whole-tree `py_compile`, an `import main` smoke test, and `scripts/check_games.py` (which
fails if any `games/<id>/` deviates from the fixed structure).

## Working style — 100% vibe coding, so structure is rigid by design

Games are built entirely by natural-language AI prompting (Claude Code / Cursor). The defense against
AI inventing its own structure is **enforced consistency**, not vigilance: `games/CLAUDE.md` +
`.cursor/rules/games.mdc` (auto-loaded when working under `games/`) state the fixed recipe, and
`make check` mechanically rejects drift. When changing how games are built, update those three in
lockstep. Always start a game from `games/_template/` via `make new-game` — never hand-roll a folder.

## Architecture

`main.py` bootstraps the FastHTML app, wires the session middleware, calls `register_routes`, and
serves the lobby `@rt("/")`. Routers live in `apps/<name>/routes.py` and are wired in
`apps/registry.py`.

### Hub (`apps/hub/`)
- `logic.py` — scans `games/*/config.json` to build the lobby (skips `_`-prefixed folders);
  score/data/log helpers over per-game tables via `utils/db_utils`.
- `routes.py` — serves game shells (`/play/{id}`, injects `window.GAME` + supabase-js + gamekit.js),
  static game assets (`/games/{id}/...`), leaderboards (`/leaderboard/{id}`), and the JSON API:
  `/api/score`, `/api/data` (POST save / GET `/api/data/{id}` load), `/api/log`, `/api/leaderboard/{id}`.

### Games (`games/<name>/`) — fixed minimal structure
**Every game is the same 4 files** (+ optional `assets/`): `config.json` (title/desc/multiplayer/
thumbnail/order), `index.html` (shell), `game.js` (logic), `style.css`. Consistency is the point —
don't invent per-game structure. `games/_template/` is the canonical starting point (uses a
`__GAME_ID__` placeholder). **Add a game with `make new-game GAME=<id>`** — it copies the template,
substitutes the id, and provisions the game's DB tables. The lobby auto-discovers it; no Python edits.

### Shared client library — `static/gamekit.js`
Common browser-side functionality lives here so games don't re-implement it. `window.GameKit` exposes:
`saveScore` / `leaderboard` / `save` / `load` / `log` (server-backed), `room(name)` (Supabase Realtime
multiplayer: `.on/.send/.onPlayers/.join`), `onInput` (keyboard+swipe), `loop(fn, fps)`, `colorFor`,
`user`. The server injects `window.GAME` (url, anon key, user, game id); gamekit builds on it. **Game
logic in `game.js` should call `GameKit.*`, not raw fetch/supabase.** Extend the library here, once.

### Data — per-game tables, identical columns (never add columns)
Each game gets its own `app_data_<id>` + `app_log_<id>`, all with the **same fixed schema** —
game-specific fields go in the `payload` JSON column, never new columns. Tables are created by the
`provision_game(p_game_id)` Postgres function (run via `make new-game` / `db_utils.provision_game`).
`user_profiles` (access_level + display_name) is the only cross-game table. Schema + the
`provision_game` function live in `migrations/001_init_schema.sql`, applied in the Supabase SQL editor.
All writes go server-side with the Supabase **service key** (RLS bypass); the browser never writes
directly. `game_id` is interpolated into table names — always validate with `db_utils.valid_game_id`.

### Auth
Supabase Auth, server-held tokens in the `bg_session` cookie. Every page route re-checks
`get_current_user(session)` and redirects to `/login` if absent. Closed system — no public signup;
provision accounts in the Supabase dashboard.

## Infra reference

| Item | Value |
|------|-------|
| GCP project | `boehringer-game-260621` |
| Cloud Run | `boehringer-game` @ `asia-northeast1` |
| Artifact Registry | `boehringer-repo` @ `asia-northeast3` |
| GCS bucket | `gs://boehringer-game-260621-assets` @ `asia-northeast1` |
| Supabase | (own project — see `.env`) |

Cloud Run env vars (set at deploy or in console): `SUPABASE_URL`, `SUPABASE_KEY`,
`SUPABASE_SERVICE_KEY`, `SECRET_KEY`.

## Conventions
- Function-oriented Python; FastHTML returns HTML fragments, no SPA framework.
- Comments explain **why**, not what. Korean docstrings, one line for public functions.
- Never commit `.env` or service-account keys (excluded in `.gitignore`/`.dockerignore`).
