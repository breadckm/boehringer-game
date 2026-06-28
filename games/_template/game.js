// __GAME_ID__ — 새 게임. 여기에 게임 로직을 만드세요.
// 공통 기능은 GameKit 으로 제공됩니다 (네트워킹·점수·입력을 다시 짤 필요 없음).
(function () {
  "use strict";

  let score = 0;
  const scoreEl = document.getElementById("score");

  document.getElementById("score-btn").addEventListener("click", function () {
    score += 10;
    scoreEl.textContent = score;
    GameKit.saveScore(score);           // 점수 저장 → 리더보드 반영
  });

  // ── 자주 쓰는 GameKit 기능 (필요한 것만 주석 풀어 사용) ──
  //
  // 키보드 + 스와이프 입력
  //   GameKit.onInput({ up(){}, down(){}, left(){}, right(){} });
  //
  // 게임 루프 (초당 10회 update 호출)
  //   const game = GameKit.loop(function () { /* 매 프레임 */ }, 10);
  //   game.stop();
  //
  // 세이브/불러오기 (게임별 테이블에 저장)
  //   GameKit.save("progress", { level: 3 });
  //   GameKit.load("progress").then(function (rows) { ... });
  //
  // 실시간 멀티플레이어
  //   const room = GameKit.room("room-1");
  //   room.on("move", function (p) { /* 상대 움직임 */ })
  //       .onPlayers(function (n) { /* 접속 인원 */ })
  //       .join();
  //   room.send("move", { x: 1, y: 2 });
  //
  // 플레이어별 고정 색상 (멀티에서 구분용)
  //   const myColor = GameKit.colorFor(GameKit.user.id);
})();
