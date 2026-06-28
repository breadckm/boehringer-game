// 스네이크 멀티플레이어 — 공통 기능은 GameKit 사용(실시간/점수/입력).
// 같은 방(room-1)에 접속한 플레이어들의 뱀이 실시간으로 함께 움직인다.
(function () {
  "use strict";

  const GRID = 30;        // 30x30 칸
  const TICK_FPS = 8;     // 초당 이동 횟수
  const STALE_MS = 3000;  // 신호 없는 상대는 화면에서 제거

  const canvas = document.getElementById("board");
  const ctx = canvas.getContext("2d");
  const cell = canvas.width / GRID;

  const scoreEl = document.getElementById("score");
  const bestEl = document.getElementById("best");
  const playersEl = document.getElementById("players");
  const overlay = document.getElementById("overlay");
  const overlayTitle = document.getElementById("overlay-title");
  const overlayMsg = document.getElementById("overlay-msg");
  const startBtn = document.getElementById("start-btn");

  const myColor = GameKit.colorFor(GameKit.user.id);
  let snake, dir, nextDir, food, score, alive, game;
  const opponents = new Map(); // id -> { name, body, color, alive, ts }

  let best = Number(localStorage.getItem("snake_best") || 0);
  bestEl.textContent = best;

  // ── 실시간 방 ──────────────────────────────────────────────
  const room = GameKit.room("room-1");
  room
    .on("state", function (p) {
      if (p.id === GameKit.user.id) return;
      opponents.set(p.id, { name: p.name, body: p.body, color: p.color, alive: p.alive, ts: Date.now() });
    })
    .onPlayers(function (n) { playersEl.textContent = "접속 " + n + "명"; })
    .join();

  function broadcast() {
    room.send("state", { id: GameKit.user.id, name: GameKit.user.name, body: snake, color: myColor, alive: alive });
  }

  // ── 게임 로직 ──────────────────────────────────────────────
  function reset() {
    snake = [{ x: 5, y: 15 }, { x: 4, y: 15 }, { x: 3, y: 15 }];
    dir = { x: 1, y: 0 };
    nextDir = { x: 1, y: 0 };
    score = 0;
    alive = true;
    placeFood();
    scoreEl.textContent = "0";
  }

  function placeFood() {
    do {
      food = { x: (Math.random() * GRID) | 0, y: (Math.random() * GRID) | 0 };
    } while (snake.some(function (s) { return s.x === food.x && s.y === food.y; }));
  }

  function tick() {
    dir = nextDir;
    const head = { x: (snake[0].x + dir.x + GRID) % GRID, y: (snake[0].y + dir.y + GRID) % GRID };
    if (snake.some(function (s) { return s.x === head.x && s.y === head.y; })) return die();

    snake.unshift(head);
    if (head.x === food.x && head.y === food.y) {
      score += 10;
      scoreEl.textContent = score;
      placeFood();
    } else {
      snake.pop();
    }
    broadcast();
    render();
  }

  function die() {
    alive = false;
    if (game) game.stop();
    broadcast();
    if (score > best) {
      best = score;
      bestEl.textContent = best;
      localStorage.setItem("snake_best", String(best));
    }
    if (score > 0) GameKit.saveScore(score);
    overlayTitle.textContent = "게임 오버";
    overlayMsg.textContent = "점수 " + score + "점 — 다시 도전!";
    startBtn.textContent = "다시 시작";
    overlay.classList.remove("hidden");
  }

  // ── 렌더링 ─────────────────────────────────────────────────
  function render() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const now = Date.now();
    opponents.forEach(function (opp, id) {
      if (now - opp.ts > STALE_MS) { opponents.delete(id); return; }
      if (!opp.body) return;
      drawSnake(opp.body, opp.color, opp.alive ? 0.55 : 0.2);
    });
    fillCircle(food.x, food.y, "#ff6b6b");
    drawSnake(snake, myColor, 1);
  }

  function drawSnake(body, color, alpha) {
    ctx.globalAlpha = alpha;
    for (let i = 0; i < body.length; i++) fillCell(body[i].x, body[i].y, color);
    ctx.globalAlpha = 1;
  }
  function fillCell(x, y, color) {
    ctx.fillStyle = color;
    ctx.fillRect(x * cell + 1, y * cell + 1, cell - 2, cell - 2);
  }
  function fillCircle(x, y, color) {
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x * cell + cell / 2, y * cell + cell / 2, cell / 2.6, 0, Math.PI * 2);
    ctx.fill();
  }

  // ── 입력 ───────────────────────────────────────────────────
  function turn(dx, dy) {
    if (dx === -dir.x && dy === -dir.y) return; // 180도 금지
    nextDir = { x: dx, y: dy };
  }
  GameKit.onInput({
    up: function () { turn(0, -1); },
    down: function () { turn(0, 1); },
    left: function () { turn(-1, 0); },
    right: function () { turn(1, 0); },
  });

  // ── 시작 ───────────────────────────────────────────────────
  function start() {
    reset();
    overlay.classList.add("hidden");
    if (game) game.stop();
    game = GameKit.loop(tick, TICK_FPS);
    render();
  }
  startBtn.addEventListener("click", start);

  // 시작 전·게임오버 상태에서도 상대 뱀을 계속 그려준다
  setInterval(function () { if (!alive || !game || !game.running()) render(); }, 200);
})();
