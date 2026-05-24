import json
from datetime import datetime
from pathlib import Path


class GameStorage:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.games_dir = self.data_dir / "games"

    def save_game(self, game):
        created = datetime.fromisoformat(game["created_at"])
        directory = self.games_dir / f"{created.year:04d}" / f"{created.month:02d}"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{created.strftime('%Y-%m-%dT%H%M%SZ')}-{game['game_id']}.json"
        path.write_text(json.dumps(game, indent=2), encoding="utf-8")
        return path

    def game_files(self):
        if not self.games_dir.exists():
            return []
        return sorted(self.games_dir.glob("*/*/*.json"), reverse=True)

    def load_game(self, game_id):
        for path in self.game_files():
            game = json.loads(path.read_text(encoding="utf-8"))
            if game["game_id"] == game_id:
                return game
        return None

    def list_games(self):
        games = []
        for path in self.game_files():
            game = json.loads(path.read_text(encoding="utf-8"))
            games.append(
                {
                    "game_id": game["game_id"],
                    "created_at": game["created_at"],
                    "black_player": game["black_player"],
                    "white_player": game["white_player"],
                    "winner": game["winner"],
                    "winner_name": game["winner_name"],
                    "final_score": game["final_score"],
                    "result_type": game["result_type"],
                    "ending_reason": game["ending_reason"],
                    "player_error": game["player_error"],
                }
            )
        return sorted(games, key=lambda game: game["created_at"], reverse=True)

    def all_games(self):
        return [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(self.game_files())
        ]
