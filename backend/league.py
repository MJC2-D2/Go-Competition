import math


def player_key(player):
    return f"{player['name']} v{player['version']}"


def ensure_record(records, player):
    key = player_key(player)
    if key not in records:
        records[key] = {
            "key": key,
            "name": player["name"],
            "version": player["version"],
            "games": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "win_rate": 0.0,
            "points": 0,
            "rating": 1000.0,
            "average_margin": 0.0,
            "illegal_moves": 0,
            "timeouts": 0,
            "crashes": 0,
            "player_errors": 0,
            "_margin_total": 0.0,
        }
    return records[key]


def expected_score(rating_a, rating_b):
    return 1.0 / (1.0 + math.pow(10.0, (rating_b - rating_a) / 400.0))


def build_league(games):
    records = {}
    k_factor = 32

    for game in sorted(games, key=lambda item: item["created_at"]):
        black = ensure_record(records, game["black_player"])
        white = ensure_record(records, game["white_player"])

        for record in (black, white):
            record["games"] += 1

        winner = game["winner"]
        if winner == "black":
            black_score, white_score = 1.0, 0.0
            black["wins"] += 1
            white["losses"] += 1
            black["points"] += 3
        elif winner == "white":
            black_score, white_score = 0.0, 1.0
            white["wins"] += 1
            black["losses"] += 1
            white["points"] += 3
        else:
            black_score, white_score = 0.5, 0.5
            black["draws"] += 1
            white["draws"] += 1
            black["points"] += 1
            white["points"] += 1

        black_expected = expected_score(black["rating"], white["rating"])
        white_expected = expected_score(white["rating"], black["rating"])
        black["rating"] += k_factor * (black_score - black_expected)
        white["rating"] += k_factor * (white_score - white_expected)

        margin = game["final_score"]["black"] - game["final_score"]["white"]
        black["_margin_total"] += margin
        white["_margin_total"] -= margin

        error = game.get("player_error")
        if error:
            errored = black if error["player_id"] == game["black_player"]["id"] else white
            errored["player_errors"] += 1
            if error["type"] == "illegal_move":
                errored["illegal_moves"] += 1
            elif error["type"] == "timeout":
                errored["timeouts"] += 1
            elif error["type"] == "exception":
                errored["crashes"] += 1

    for record in records.values():
        if record["games"]:
            record["win_rate"] = record["wins"] / record["games"]
            record["average_margin"] = record["_margin_total"] / record["games"]
        record["rating"] = round(record["rating"], 1)
        record["win_rate"] = round(record["win_rate"], 3)
        record["average_margin"] = round(record["average_margin"], 2)
        del record["_margin_total"]

    return sorted(records.values(), key=lambda record: record["rating"], reverse=True)
