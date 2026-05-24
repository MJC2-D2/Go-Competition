import React from 'react';
import { createRoot } from 'react-dom/client';
import {
  BarChart3,
  CirclePlay,
  History,
  ListOrdered,
  RefreshCw,
  StepBack,
  StepForward,
} from 'lucide-react';
import './styles.css';

const API_BASE = 'http://127.0.0.1:8000';

function emptyBoard(size = 9) {
  return Array.from({ length: size }, () => Array.from({ length: size }, () => 0));
}

function formatScore(score) {
  if (!score) return '';
  return `B ${score.black} - W ${score.white}`;
}

function playerLabel(player) {
  return player ? `${player.name} v${player.version}` : '';
}

function App() {
  const [players, setPlayers] = React.useState([]);
  const [jobs, setJobs] = React.useState([]);
  const [games, setGames] = React.useState([]);
  const [league, setLeague] = React.useState([]);
  const [selectedGame, setSelectedGame] = React.useState(null);
  const [historyFilter, setHistoryFilter] = React.useState('');
  const [activeTab, setActiveTab] = React.useState('run');
  const [leagueSort, setLeagueSort] = React.useState({ key: 'rating', direction: 'desc' });
  const [moveIndex, setMoveIndex] = React.useState(0);
  const [form, setForm] = React.useState({
    black_player_id: '',
    white_player_id: '',
    games: 2,
    komi: 6.5,
    max_move_count: 250,
  });
  const [message, setMessage] = React.useState('');

  const playablePlayers = players.filter((player) => player.status === 'ok');

  async function fetchJson(path, options) {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Request failed');
    }
    return data;
  }

  async function refresh() {
    const [nextPlayers, nextJobs, nextGames, nextLeague] = await Promise.all([
      fetchJson('/api/players'),
      fetchJson('/api/jobs'),
      fetchJson(`/api/games${historyFilter ? `?player=${encodeURIComponent(historyFilter)}` : ''}`),
      fetchJson('/api/league'),
    ]);
    setPlayers(nextPlayers);
    setJobs(nextJobs);
    setGames(nextGames);
    setLeague(nextLeague);

    if (!form.black_player_id && nextPlayers.length > 0) {
      const first = nextPlayers.find((player) => player.status === 'ok');
      const second = nextPlayers.filter((player) => player.status === 'ok')[1] || first;
      if (first) {
        setForm((current) => ({
          ...current,
          black_player_id: first.id,
          white_player_id: second.id,
        }));
      }
    }
  }

  React.useEffect(() => {
    refresh().catch((error) => setMessage(error.message));
  }, [historyFilter]);

  React.useEffect(() => {
    const interval = window.setInterval(() => {
      refresh().catch(() => {});
    }, 2500);
    return () => window.clearInterval(interval);
  });

  async function queueMatch(event) {
    event.preventDefault();
    setMessage('');
    try {
      const job = await fetchJson('/api/matches', {
        method: 'POST',
        body: JSON.stringify({
          ...form,
          games: Number(form.games),
          komi: Number(form.komi),
          max_move_count: Number(form.max_move_count),
        }),
      });
      setMessage(`Queued ${job.games} game${job.games === 1 ? '' : 's'} as ${job.id}.`);
      await refresh();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function openGame(gameId) {
    const game = await fetchJson(`/api/games/${gameId}`);
    setSelectedGame(game);
    setMoveIndex(game.moves.length);
    setActiveTab('replay');
  }

  const sortedLeague = [...league].sort((a, b) => {
    const direction = leagueSort.direction === 'asc' ? 1 : -1;
    const aValue = a[leagueSort.key];
    const bValue = b[leagueSort.key];
    if (typeof aValue === 'string') {
      return aValue.localeCompare(bValue) * direction;
    }
    return ((aValue || 0) - (bValue || 0)) * direction;
  });

  function sortLeague(key) {
    setLeagueSort((current) => ({
      key,
      direction: current.key === key && current.direction === 'desc' ? 'asc' : 'desc',
    }));
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Go Competition</h1>
          <p>9x9 area-scored Python player arena</p>
        </div>
        <button className="icon-button" type="button" onClick={refresh} title="Refresh">
          <RefreshCw size={18} />
        </button>
      </header>

      <nav className="tabs" aria-label="Views">
        <Tab active={activeTab === 'run'} onClick={() => setActiveTab('run')} icon={<CirclePlay size={16} />} label="Run" />
        <Tab active={activeTab === 'history'} onClick={() => setActiveTab('history')} icon={<History size={16} />} label="History" />
        <Tab active={activeTab === 'replay'} onClick={() => setActiveTab('replay')} icon={<ListOrdered size={16} />} label="Replay" />
        <Tab active={activeTab === 'league'} onClick={() => setActiveTab('league')} icon={<BarChart3 size={16} />} label="League" />
      </nav>

      {message && <div className="notice">{message}</div>}

      {activeTab === 'run' && (
        <section className="layout-two">
          <form className="panel" onSubmit={queueMatch}>
            <h2>Run Match</h2>
            <label>
              Black player
              <select value={form.black_player_id} onChange={(event) => setForm({ ...form, black_player_id: event.target.value })}>
                {playablePlayers.map((player) => (
                  <option key={player.id} value={player.id}>{playerLabel(player)}</option>
                ))}
              </select>
            </label>
            <label>
              White player
              <select value={form.white_player_id} onChange={(event) => setForm({ ...form, white_player_id: event.target.value })}>
                {playablePlayers.map((player) => (
                  <option key={player.id} value={player.id}>{playerLabel(player)}</option>
                ))}
              </select>
            </label>
            <div className="field-row">
              <label>
                Games
                <input type="number" min="1" max="100" value={form.games} onChange={(event) => setForm({ ...form, games: event.target.value })} />
              </label>
              <label>
                Komi
                <input type="number" step="0.5" value={form.komi} onChange={(event) => setForm({ ...form, komi: event.target.value })} />
              </label>
              <label>
                Max moves
                <input type="number" min="1" max="1000" value={form.max_move_count} onChange={(event) => setForm({ ...form, max_move_count: event.target.value })} />
              </label>
            </div>
            <button className="primary-button" type="submit">Queue Match</button>
          </form>

          <section className="panel">
            <h2>Jobs</h2>
            <div className="list">
              {jobs.length === 0 && <p className="muted">No jobs queued.</p>}
              {jobs.map((job) => (
                <div className="list-row" key={job.id}>
                  <div>
                    <strong>{job.id}</strong>
                    <span>{job.status} · {job.completed_games}/{job.games} games</span>
                  </div>
                  {job.error && <span className="error-text">{job.error}</span>}
                </div>
              ))}
            </div>
          </section>
        </section>
      )}

      {activeTab === 'history' && (
        <section className="panel">
          <div className="section-header">
            <h2>Game History</h2>
            <input className="filter-input" placeholder="Filter by player" value={historyFilter} onChange={(event) => setHistoryFilter(event.target.value)} />
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Black</th>
                  <th>White</th>
                  <th>Score</th>
                  <th>Result</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {games.map((game) => (
                  <tr key={game.game_id}>
                    <td>{new Date(game.created_at).toLocaleString()}</td>
                    <td>{playerLabel(game.black_player)}</td>
                    <td>{playerLabel(game.white_player)}</td>
                    <td>{formatScore(game.final_score)}</td>
                    <td>{game.winner_name || 'Draw'} · {game.ending_reason}</td>
                    <td><button type="button" onClick={() => openGame(game.game_id)}>Open</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {activeTab === 'replay' && (
        <Replay game={selectedGame} moveIndex={moveIndex} setMoveIndex={setMoveIndex} />
      )}

      {activeTab === 'league' && (
        <section className="panel">
          <h2>League Table</h2>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {[
                    ['name', 'Player'],
                    ['games', 'Games'],
                    ['wins', 'Wins'],
                    ['losses', 'Losses'],
                    ['draws', 'Draws'],
                    ['win_rate', 'Win rate'],
                    ['points', 'Points'],
                    ['rating', 'Elo'],
                    ['average_margin', 'Avg margin'],
                    ['illegal_moves', 'Illegal'],
                    ['timeouts', 'Timeouts'],
                    ['crashes', 'Crashes'],
                    ['player_errors', 'Errors'],
                  ].map(([key, label]) => (
                    <th key={key}><button type="button" onClick={() => sortLeague(key)}>{label}</button></th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedLeague.map((record) => (
                  <tr key={record.key}>
                    <td>{record.name} v{record.version}</td>
                    <td>{record.games}</td>
                    <td>{record.wins}</td>
                    <td>{record.losses}</td>
                    <td>{record.draws}</td>
                    <td>{record.win_rate}</td>
                    <td>{record.points}</td>
                    <td>{record.rating}</td>
                    <td>{record.average_margin}</td>
                    <td>{record.illegal_moves}</td>
                    <td>{record.timeouts}</td>
                    <td>{record.crashes}</td>
                    <td>{record.player_errors}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </main>
  );
}

function Tab({ active, onClick, icon, label }) {
  return (
    <button className={active ? 'tab active' : 'tab'} type="button" onClick={onClick}>
      {icon}
      <span>{label}</span>
    </button>
  );
}

function Replay({ game, moveIndex, setMoveIndex }) {
  if (!game) {
    return (
      <section className="panel empty-state">
        <h2>Replay</h2>
        <p>Select a game from history to inspect the moves.</p>
      </section>
    );
  }

  const board = moveIndex === 0 ? emptyBoard(game.board_size) : game.moves[moveIndex - 1].board;
  const currentMove = moveIndex === 0 ? null : game.moves[moveIndex - 1];
  const ownership = moveIndex === game.moves.length ? game.final_scoring_ownership : null;

  return (
    <section className="replay-layout">
      <div className="panel board-panel">
        <Board board={board} ownership={ownership} />
      </div>
      <aside className="panel replay-side">
        <h2>Replay</h2>
        <dl className="facts">
          <dt>Black</dt>
          <dd>{playerLabel(game.black_player)}</dd>
          <dt>White</dt>
          <dd>{playerLabel(game.white_player)}</dd>
          <dt>Score</dt>
          <dd>{formatScore(game.final_score)}</dd>
          <dt>Result</dt>
          <dd>{game.winner_name || 'Draw'} · {game.ending_reason}</dd>
        </dl>
        <div className="move-controls">
          <button className="icon-button" type="button" title="Previous move" onClick={() => setMoveIndex(Math.max(0, moveIndex - 1))}>
            <StepBack size={18} />
          </button>
          <input type="range" min="0" max={game.moves.length} value={moveIndex} onChange={(event) => setMoveIndex(Number(event.target.value))} />
          <button className="icon-button" type="button" title="Next move" onClick={() => setMoveIndex(Math.min(game.moves.length, moveIndex + 1))}>
            <StepForward size={18} />
          </button>
        </div>
        <p className="move-label">
          Move {moveIndex} of {game.moves.length}
          {currentMove ? ` · ${currentMove.color} ${currentMove.move ? currentMove.move.join(', ') : 'passed'}` : ''}
        </p>
        {game.player_error && (
          <p className="error-text">{game.player_error.player}: {game.player_error.message}</p>
        )}
      </aside>
    </section>
  );
}

function Board({ board, ownership }) {
  return (
    <div className="go-board" style={{ '--board-size': board.length }}>
      {board.map((row, rowIndex) => row.map((point, colIndex) => {
        const owner = ownership?.[rowIndex]?.[colIndex] || 0;
        return (
          <div className={`intersection owner-${owner}`} key={`${rowIndex}-${colIndex}`}>
            {point === 1 && <span className="stone white-stone" />}
            {point === 2 && <span className="stone black-stone" />}
          </div>
        );
      }))}
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
