const state = {
  players: [],
  jobs: [],
  games: [],
  league: [],
  selectedGame: null,
  activeTab: "run",
  moveIndex: 0,
  leagueSort: { key: "rating", direction: "desc" },
};

const leagueColumns = [
  ["name", "Player"],
  ["games", "Games"],
  ["wins", "Wins"],
  ["losses", "Losses"],
  ["draws", "Draws"],
  ["win_rate", "Win rate"],
  ["points", "Points"],
  ["rating", "Elo"],
  ["average_margin", "Avg margin"],
  ["illegal_moves", "Illegal"],
  ["timeouts", "Timeouts"],
  ["crashes", "Crashes"],
  ["player_errors", "Errors"],
];

function byId(id) {
  return document.getElementById(id);
}

function emptyBoard(size) {
  return Array.from({ length: size }, () => Array.from({ length: size }, () => 0));
}

function playerLabel(player) {
  return player ? `${player.name} v${player.version}` : "";
}

function formatScore(score) {
  return score ? `B ${score.black} - W ${score.white}` : "";
}

function setNotice(message) {
  const notice = byId("notice");
  notice.textContent = message || "";
  notice.classList.toggle("hidden", !message);
}

async function fetchJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

async function refresh() {
  const filter = byId("historyFilter").value.trim();
  const [players, jobs, games, league] = await Promise.all([
    fetchJson("/api/players"),
    fetchJson("/api/jobs"),
    fetchJson(`/api/games${filter ? `?player=${encodeURIComponent(filter)}` : ""}`),
    fetchJson("/api/league"),
  ]);

  state.players = players;
  state.jobs = jobs;
  state.games = games;
  state.league = league;

  renderPlayers();
  renderJobs();
  renderGames();
  renderLeague();
  renderReplay();
}

function renderPlayers() {
  const playable = state.players.filter((player) => player.status === "ok");
  const blackSelect = byId("blackPlayer");
  const whiteSelect = byId("whitePlayer");
  const currentBlack = blackSelect.value;
  const currentWhite = whiteSelect.value;

  blackSelect.innerHTML = "";
  whiteSelect.innerHTML = "";

  for (const player of playable) {
    blackSelect.appendChild(new Option(playerLabel(player), player.id));
    whiteSelect.appendChild(new Option(playerLabel(player), player.id));
  }

  if (playable.some((player) => player.id === currentBlack)) {
    blackSelect.value = currentBlack;
  }
  if (playable.some((player) => player.id === currentWhite)) {
    whiteSelect.value = currentWhite;
  } else if (playable[1]) {
    whiteSelect.value = playable[1].id;
  }
}

function renderJobs() {
  const list = byId("jobsList");
  list.innerHTML = "";

  if (state.jobs.length === 0) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No jobs queued.";
    list.appendChild(empty);
    return;
  }

  for (const job of state.jobs) {
    const row = document.createElement("div");
    row.className = "list-row";
    const summary = document.createElement("div");
    summary.innerHTML = `<strong>${job.id}</strong><span>${job.status} - ${job.completed_games}/${job.games} games</span>`;
    row.appendChild(summary);
    if (job.error) {
      const error = document.createElement("span");
      error.className = "error-text";
      error.textContent = job.error;
      row.appendChild(error);
    }
    list.appendChild(row);
  }
}

function renderGames() {
  const table = byId("gamesTable");
  table.innerHTML = "";

  for (const game of state.games) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${new Date(game.created_at).toLocaleString()}</td>
      <td>${playerLabel(game.black_player)}</td>
      <td>${playerLabel(game.white_player)}</td>
      <td>${formatScore(game.final_score)}</td>
      <td>${game.winner_name || "Draw"} - ${game.ending_reason}</td>
      <td><button type="button" data-game-id="${game.game_id}">Open</button></td>
    `;
    row.querySelector("button").addEventListener("click", () => openGame(game.game_id));
    table.appendChild(row);
  }
}

function renderLeague() {
  const header = byId("leagueHeader");
  const table = byId("leagueTable");
  header.innerHTML = "";
  table.innerHTML = "";

  for (const [key, label] of leagueColumns) {
    const cell = document.createElement("th");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", () => sortLeague(key));
    cell.appendChild(button);
    header.appendChild(cell);
  }

  const sorted = [...state.league].sort((a, b) => {
    const direction = state.leagueSort.direction === "asc" ? 1 : -1;
    const left = a[state.leagueSort.key];
    const right = b[state.leagueSort.key];
    if (typeof left === "string") {
      return left.localeCompare(right) * direction;
    }
    return ((left || 0) - (right || 0)) * direction;
  });

  for (const record of sorted) {
    const row = document.createElement("tr");
    const values = [
      `${record.name} v${record.version}`,
      record.games,
      record.wins,
      record.losses,
      record.draws,
      record.win_rate,
      record.points,
      record.rating,
      record.average_margin,
      record.illegal_moves,
      record.timeouts,
      record.crashes,
      record.player_errors,
    ];
    row.innerHTML = values.map((value) => `<td>${value}</td>`).join("");
    table.appendChild(row);
  }
}

function sortLeague(key) {
  state.leagueSort = {
    key,
    direction:
      state.leagueSort.key === key && state.leagueSort.direction === "desc"
        ? "asc"
        : "desc",
  };
  renderLeague();
}

async function queueMatch(event) {
  event.preventDefault();
  setNotice("");

  try {
    const job = await fetchJson("/api/matches", {
      method: "POST",
      body: JSON.stringify({
        black_player_id: byId("blackPlayer").value,
        white_player_id: byId("whitePlayer").value,
        games: Number(byId("gameCount").value),
        komi: Number(byId("komi").value),
        max_move_count: Number(byId("maxMoveCount").value),
      }),
    });
    setNotice(`Queued ${job.games} game${job.games === 1 ? "" : "s"} as ${job.id}.`);
    await refresh();
  } catch (error) {
    setNotice(error.message);
  }
}

async function openGame(gameId) {
  state.selectedGame = await fetchJson(`/api/games/${gameId}`);
  state.moveIndex = state.selectedGame.moves.length;
  switchTab("replay");
  renderReplay();
}

function renderReplay() {
  const game = state.selectedGame;

  if (!game) {
    drawBoard(emptyBoard(9), null);
    byId("moveSlider").max = "0";
    byId("moveSlider").value = "0";
    return;
  }

  const board = state.moveIndex === 0 ? emptyBoard(game.board_size) : game.moves[state.moveIndex - 1].board;
  const ownership = state.moveIndex === game.moves.length ? game.final_scoring_ownership : null;
  const currentMove = state.moveIndex === 0 ? null : game.moves[state.moveIndex - 1];

  drawBoard(board, ownership);
  byId("replayBlack").textContent = playerLabel(game.black_player);
  byId("replayWhite").textContent = playerLabel(game.white_player);
  byId("replayScore").textContent = formatScore(game.final_score);
  byId("replayResult").textContent = `${game.winner_name || "Draw"} - ${game.ending_reason}`;
  byId("moveSlider").max = String(game.moves.length);
  byId("moveSlider").value = String(state.moveIndex);
  byId("moveLabel").textContent =
    `Move ${state.moveIndex} of ${game.moves.length}` +
    (currentMove ? ` - ${currentMove.color} ${currentMove.move ? currentMove.move.join(", ") : "passed"}` : "");

  const replayError = byId("replayError");
  if (game.player_error) {
    replayError.textContent = `${game.player_error.player}: ${game.player_error.message}`;
    replayError.classList.remove("hidden");
  } else {
    replayError.classList.add("hidden");
  }
}

function drawBoard(board, ownership) {
  const element = byId("goBoard");
  element.style.setProperty("--board-size", board.length);
  element.innerHTML = "";

  for (let row = 0; row < board.length; row += 1) {
    for (let col = 0; col < board[row].length; col += 1) {
      const point = document.createElement("div");
      const owner = ownership?.[row]?.[col] || 0;
      point.className = `intersection owner-${owner}`;

      if (board[row][col] === 1 || board[row][col] === 2) {
        const stone = document.createElement("span");
        stone.className = board[row][col] === 1 ? "stone white-stone" : "stone black-stone";
        point.appendChild(stone);
      }

      element.appendChild(point);
    }
  }
}

function switchTab(tab) {
  state.activeTab = tab;

  document.querySelectorAll(".tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === tab);
  });
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.add("hidden");
  });
  byId(`${tab}View`).classList.remove("hidden");
}

function setMoveIndex(nextIndex) {
  if (!state.selectedGame) {
    return;
  }
  state.moveIndex = Math.max(0, Math.min(state.selectedGame.moves.length, nextIndex));
  renderReplay();
}

function setupEvents() {
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  });
  byId("refreshButton").addEventListener("click", () => refresh().catch((error) => setNotice(error.message)));
  byId("matchForm").addEventListener("submit", queueMatch);
  byId("historyFilter").addEventListener("input", () => refresh().catch((error) => setNotice(error.message)));
  byId("previousMove").addEventListener("click", () => setMoveIndex(state.moveIndex - 1));
  byId("nextMove").addEventListener("click", () => setMoveIndex(state.moveIndex + 1));
  byId("moveSlider").addEventListener("input", (event) => setMoveIndex(Number(event.target.value)));
}

setupEvents();
drawBoard(emptyBoard(9), null);
refresh().catch((error) => setNotice(error.message));
window.setInterval(() => refresh().catch(() => {}), 2500);
