// GameKit — 모든 미니게임이 공유하는 라이브러리.
// 서버가 주입한 window.GAME(설정·유저) 위에 공통 기능을 얹는다.
// 게임 코드(game.js)는 네트워킹·점수·입력을 다시 짜지 않고 GameKit.* 만 호출한다.
(function () {
  "use strict";

  const G = window.GAME || { id: "unknown", user: { id: "local", name: "나" } };
  const sb = (G.supabaseUrl && window.supabase)
    ? window.supabase.createClient(G.supabaseUrl, G.supabaseAnonKey)
    : null;

  function postJSON(url, data) {
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(Object.assign({ game_id: G.id }, data)),
    }).then((r) => r.json());
  }

  const GameKit = {
    // ── 기본 정보 ──────────────────────────────────────────
    id: G.id,
    user: G.user,            // { id, name }
    supabase: sb,            // 필요하면 직접 사용 가능

    // ── 점수 / 데이터 / 로그 (서버 경유, 게임별 테이블에 저장) ──
    saveScore(score) { return postJSON("/api/score", { score: score }); },
    leaderboard(limit = 10) {
      return fetch(`/api/leaderboard/${G.id}`).then((r) => r.json()).then((d) => d.rows || []);
    },
    save(dataType, payload) { return postJSON("/api/data", { data_type: dataType, payload: payload }); },
    load(dataType = "default") {
      return fetch(`/api/data/${G.id}?data_type=${encodeURIComponent(dataType)}`)
        .then((r) => r.json()).then((d) => d.rows || []);
    },
    log(event, payload) { return postJSON("/api/log", { event: event, payload: payload || {} }); },

    // ── 실시간 멀티플레이어 ──────────────────────────────────
    // const room = GameKit.room("room-1");
    // room.on("move", (p) => {...}); room.send("move", {x,y}); room.onPlayers((n)=>{...});
    room(name) {
      if (!sb) return _offlineRoom();
      const ch = sb.channel(`${G.id}:${name}`, {
        config: { broadcast: { self: false }, presence: { key: G.user.id } },
      });
      let playersCb = null;
      ch.on("presence", { event: "sync" }, () => {
        if (playersCb) playersCb(Object.keys(ch.presenceState()).length);
      });
      const api = {
        on(event, cb) {
          ch.on("broadcast", { event: event }, (m) => cb(m.payload));
          return api;
        },
        send(event, payload) {
          ch.send({ type: "broadcast", event: event, payload: payload });
          return api;
        },
        onPlayers(cb) { playersCb = cb; return api; },
        join() { ch.subscribe((s) => { if (s === "SUBSCRIBED") ch.track({ name: G.user.name }); }); return api; },
        leave() { sb.removeChannel(ch); },
      };
      return api;
    },

    // ── 입력 (키보드 + 스와이프 통합) ────────────────────────
    // GameKit.onInput({ up(){}, down(){}, left(){}, right(){} })
    onInput(handlers) {
      const KEY = {
        ArrowUp: "up", ArrowDown: "down", ArrowLeft: "left", ArrowRight: "right",
        w: "up", s: "down", a: "left", d: "right",
      };
      window.addEventListener("keydown", (e) => {
        const dir = KEY[e.key];
        if (dir && handlers[dir]) { e.preventDefault(); handlers[dir](); }
      });
      let start = null;
      const el = document.body;
      el.addEventListener("touchstart", (e) => { start = e.touches[0]; }, { passive: true });
      el.addEventListener("touchend", (e) => {
        if (!start) return;
        const t = e.changedTouches[0];
        const dx = t.clientX - start.clientX, dy = t.clientY - start.clientY;
        start = null;
        if (Math.abs(dx) < 24 && Math.abs(dy) < 24) return;
        const dir = Math.abs(dx) > Math.abs(dy)
          ? (dx > 0 ? "right" : "left")
          : (dy > 0 ? "down" : "up");
        if (handlers[dir]) handlers[dir]();
      }, { passive: true });
    },

    // ── 게임 루프 (초당 fps회 update 호출) ──────────────────
    loop(update, fps = 10) {
      let timer = setInterval(update, 1000 / fps);
      return { stop() { clearInterval(timer); timer = null; }, running() { return timer !== null; } };
    },

    // ── 색상 — 같은 id면 항상 같은 색 (멀티에서 플레이어 구분) ──
    colorFor(seed) {
      seed = String(seed || G.user.id);
      let h = 0;
      for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
      return `hsl(${h % 360}, 70%, 60%)`;
    },
  };

  function _offlineRoom() {
    // Supabase가 없을 때(직접 열기 등) 안전하게 동작하는 빈 방
    const api = { on() { return api; }, send() { return api; }, onPlayers() { return api; }, join() { return api; }, leave() {} };
    return api;
  }

  window.GameKit = GameKit;
})();
