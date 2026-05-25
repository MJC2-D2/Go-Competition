import tempfile
import textwrap
import unittest
from pathlib import Path

from backend.player_loader import PlayerLoadError, PlayerLoader


class PlayerLoaderTest(unittest.TestCase):
    def test_load_player_instantiates_player_class(self):
        with tempfile.TemporaryDirectory() as directory:
            players_dir = Path(directory)
            (players_dir / "stateful.py").write_text(
                textwrap.dedent(
                    """
                    class Player:
                        def __init__(self):
                            self.moves_seen = 0

                        def name(self):
                            return "Stateful"

                        def version(self):
                            return "1.0"

                        def select_move(self, color, board, preview_move, get_legal_moves):
                            self.moves_seen += 1
                            return None
                    """
                ),
                encoding="utf-8",
            )

            loader = PlayerLoader(players_dir)
            first = loader.load_player("stateful")
            second = loader.load_player("stateful")

            self.assertEqual(first.name, "Stateful")
            self.assertEqual(first.version, "1.0")
            self.assertIsNot(first.instance, second.instance)
            first.instance.select_move(2, (), None, lambda color, board: ())
            self.assertEqual(first.instance.moves_seen, 1)
            self.assertEqual(second.instance.moves_seen, 0)

    def test_load_player_requires_player_class(self):
        with tempfile.TemporaryDirectory() as directory:
            players_dir = Path(directory)
            (players_dir / "legacy.py").write_text(
                textwrap.dedent(
                    """
                    def name():
                        return "Legacy"

                    def version():
                        return "1.0"

                    def select_move(color, board, preview_move, get_legal_moves):
                        return None
                    """
                ),
                encoding="utf-8",
            )

            loader = PlayerLoader(players_dir)

            with self.assertRaisesRegex(PlayerLoadError, "Missing required class: Player"):
                loader.load_player("legacy")


if __name__ == "__main__":
    unittest.main()
