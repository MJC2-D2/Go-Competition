import importlib.util
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LoadedPlayer:
    id: str
    name: str
    version: str
    instance: object


class PlayerLoadError(Exception):
    pass


class PlayerLoader:
    def __init__(self, players_dir):
        self.players_dir = Path(players_dir)

    def player_files(self):
        if not self.players_dir.exists():
            return []
        return sorted(
            path
            for path in self.players_dir.glob("*.py")
            if not path.name.startswith("_")
        )

    def list_players(self):
        players = []
        seen_names = set()

        for path in self.player_files():
            player_id = path.stem
            try:
                player = self.load_player(player_id)
                status = "ok"
                error = None
                if player.name in seen_names:
                    status = "error"
                    error = f"Duplicate player name: {player.name}"
                seen_names.add(player.name)
                players.append(
                    {
                        "id": player.id,
                        "name": player.name,
                        "version": player.version,
                        "status": status,
                        "error": error,
                    }
                )
            except PlayerLoadError as exc:
                players.append(
                    {
                        "id": player_id,
                        "name": player_id,
                        "version": "",
                        "status": "error",
                        "error": str(exc),
                    }
                )

        return players

    def load_player(self, player_id):
        if "/" in player_id or "\\" in player_id or player_id.startswith("."):
            raise PlayerLoadError("Invalid player id.")

        path = self.players_dir / f"{player_id}.py"
        if not path.exists():
            raise PlayerLoadError(f"Player not found: {player_id}")

        module_name = f"go_competition_player_{player_id}_{path.stat().st_mtime_ns}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise PlayerLoadError(f"Unable to import player: {player_id}")

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            raise PlayerLoadError(f"Player import failed: {exc}") from exc

        player_class = getattr(module, "Player", None)
        if not callable(player_class):
            raise PlayerLoadError("Missing required class: Player")

        try:
            instance = player_class()
        except Exception as exc:
            raise PlayerLoadError(f"Player instantiation failed: {exc}") from exc

        for method_name in ("name", "version", "select_move"):
            if not callable(getattr(instance, method_name, None)):
                raise PlayerLoadError(f"Missing required method: Player.{method_name}()")

        try:
            name = instance.name()
            version = instance.version()
        except Exception as exc:
            raise PlayerLoadError(f"Player metadata failed: {exc}") from exc

        if not isinstance(name, str) or not name.strip():
            raise PlayerLoadError("Player name must be a non-empty string.")
        if not isinstance(version, str) or not version.strip():
            raise PlayerLoadError("Player version must be a non-empty string.")

        return LoadedPlayer(player_id, name.strip(), version.strip(), instance)
