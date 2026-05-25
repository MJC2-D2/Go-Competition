import unittest

from backend.league import build_league


def player(player_id, name, version):
    return {"id": player_id, "name": name, "version": version}


def game(created_at, black_player, white_player, winner="black"):
    return {
        "created_at": created_at,
        "black_player": black_player,
        "white_player": white_player,
        "winner": winner,
        "final_score": {"black": 10.0, "white": 5.0},
        "player_error": None,
    }


class LeagueTest(unittest.TestCase):
    def test_excludes_self_play_with_same_name_and_version(self):
        same_v1 = player("same_a", "Same Player", "1.0")
        same_v1_alias = player("same_b", "Same Player", "1.0")
        other = player("other", "Other Player", "1.0")

        league = build_league(
            [
                game("2026-05-24T10:00:00+00:00", same_v1, same_v1_alias),
                game("2026-05-24T11:00:00+00:00", same_v1, other),
            ]
        )

        records = {record["key"]: record for record in league}

        self.assertEqual(records["Same Player v1.0"]["games"], 1)
        self.assertEqual(records["Same Player v1.0"]["wins"], 1)
        self.assertEqual(records["Other Player v1.0"]["games"], 1)
        self.assertEqual(records["Other Player v1.0"]["losses"], 1)


if __name__ == "__main__":
    unittest.main()
