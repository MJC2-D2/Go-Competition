import json
import queue
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .league import build_league
from .player_loader import PlayerLoader
from .runner import GameRunner
from .storage import GameStorage


ROOT = Path(__file__).resolve().parents[1]
PLAYERS_DIR = ROOT / "players"
DATA_DIR = ROOT / "data"


@dataclass
class MatchJob:
    id: str
    black_player_id: str
    white_player_id: str
    games: int
    komi: float
    max_move_count: int
    status: str = "queued"
    completed_games: int = 0
    game_ids: list = field(default_factory=list)
    error: str | None = None


class AppState:
    def __init__(self):
        self.player_loader = PlayerLoader(PLAYERS_DIR)
        self.storage = GameStorage(DATA_DIR)
        self.runner = GameRunner(size=9)
        self.jobs = {}
        self.job_queue = queue.Queue()
        self.lock = threading.Lock()
        self.worker = threading.Thread(target=self._work, daemon=True)
        self.worker.start()

    def enqueue_match(self, black_player_id, white_player_id, games, komi, max_move_count):
        job_id = f"job-{len(self.jobs) + 1}"
        job = MatchJob(
            id=job_id,
            black_player_id=black_player_id,
            white_player_id=white_player_id,
            games=games,
            komi=komi,
            max_move_count=max_move_count,
        )
        with self.lock:
            self.jobs[job_id] = job
        self.job_queue.put(job_id)
        return self.serialize_job(job)

    def get_job(self, job_id):
        with self.lock:
            job = self.jobs.get(job_id)
            return self.serialize_job(job) if job else None

    def list_jobs(self):
        with self.lock:
            return [self.serialize_job(job) for job in self.jobs.values()]

    def serialize_job(self, job):
        return {
            "id": job.id,
            "black_player_id": job.black_player_id,
            "white_player_id": job.white_player_id,
            "games": job.games,
            "komi": job.komi,
            "max_move_count": job.max_move_count,
            "status": job.status,
            "completed_games": job.completed_games,
            "game_ids": job.game_ids,
            "error": job.error,
        }

    def _update_job(self, job_id, **changes):
        with self.lock:
            job = self.jobs[job_id]
            for key, value in changes.items():
                setattr(job, key, value)

    def _work(self):
        while True:
            job_id = self.job_queue.get()
            with self.lock:
                job = self.jobs[job_id]
            self._update_job(job_id, status="running")

            try:
                for index in range(job.games):
                    if index % 2 == 0:
                        black_id = job.black_player_id
                        white_id = job.white_player_id
                    else:
                        black_id = job.white_player_id
                        white_id = job.black_player_id

                    black_player = self.player_loader.load_player(black_id)
                    white_player = self.player_loader.load_player(white_id)
                    game = self.runner.run_game(
                        black_player,
                        white_player,
                        komi=job.komi,
                        max_move_count=job.max_move_count,
                    )
                    self.storage.save_game(game)

                    with self.lock:
                        stored_job = self.jobs[job_id]
                        stored_job.completed_games += 1
                        stored_job.game_ids.append(game["game_id"])

                self._update_job(job_id, status="complete")
            except Exception as exc:
                self._update_job(job_id, status="failed", error=str(exc))
            finally:
                self.job_queue.task_done()


STATE = AppState()


class ApiHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path == "/api/players":
            return self.write_json(STATE.player_loader.list_players())
        if path == "/api/jobs":
            return self.write_json(STATE.list_jobs())
        if path.startswith("/api/jobs/"):
            job = STATE.get_job(path.rsplit("/", 1)[-1])
            return self.write_json_or_404(job)
        if path == "/api/games":
            games = STATE.storage.list_games()
            player_filter = query.get("player", [""])[0].lower().strip()
            if player_filter:
                games = [
                    game
                    for game in games
                    if player_filter in game["black_player"]["name"].lower()
                    or player_filter in game["white_player"]["name"].lower()
                ]
            return self.write_json(games)
        if path.startswith("/api/games/"):
            game = STATE.storage.load_game(path.rsplit("/", 1)[-1])
            return self.write_json_or_404(game)
        if path == "/api/league":
            return self.write_json(build_league(STATE.storage.all_games()))
        if path == "/api/health":
            return self.write_json({"status": "ok"})

        self.write_json({"error": "Not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/matches":
            return self.write_json({"error": "Not found"}, status=404)

        try:
            body = self.read_json()
            black_player_id = str(body["black_player_id"])
            white_player_id = str(body["white_player_id"])
            games = int(body.get("games", 1))
            komi = float(body.get("komi", 6.5))
            max_move_count = int(body.get("max_move_count", 250))
            if games < 1 or games > 100:
                raise ValueError("games must be between 1 and 100")
            if max_move_count < 1 or max_move_count > 1000:
                raise ValueError("max_move_count must be between 1 and 1000")

            STATE.player_loader.load_player(black_player_id)
            STATE.player_loader.load_player(white_player_id)
            job = STATE.enqueue_match(
                black_player_id,
                white_player_id,
                games,
                komi,
                max_move_count,
            )
            self.write_json(job, status=202)
        except Exception as exc:
            self.write_json({"error": str(exc)}, status=400)

    def read_json(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def write_json_or_404(self, value):
        if value is None:
            return self.write_json({"error": "Not found"}, status=404)
        return self.write_json(value)

    def write_json(self, value, status=200):
        payload = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format, *args):
        return


def run(host="127.0.0.1", port=8000):
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"Backend API running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
