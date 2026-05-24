import uuid
from datetime import datetime, timezone

from .go_engine import BLACK, WHITE, legal_moves, new_board, play_move, score_area


COLOR_NAMES = {
    BLACK: "black",
    WHITE: "white",
}


def json_board(board):
    return [list(row) for row in board]


def json_move(move):
    if move is None:
        return None
    return [move[0], move[1]]


class GameRunner:
    def __init__(self, size=9):
        self.size = size

    def run_game(self, black_player, white_player, komi=6.5, max_move_count=250):
        game_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        board = new_board(self.size)
        previous_positions = {board}
        consecutive_passes = 0
        captures = {"black": 0, "white": 0}
        moves = []
        players_by_color = {
            BLACK: black_player,
            WHITE: white_player,
        }
        ending_reason = None
        player_error = None

        for turn_number in range(1, max_move_count + 1):
            color = BLACK if turn_number % 2 == 1 else WHITE
            player = players_by_color[color]
            available_moves = legal_moves(board, color, previous_positions)

            def preview_move(move):
                if move not in available_moves:
                    raise ValueError("Only legal moves can be previewed.")
                preview_board, _ = play_move(board, color, move, previous_positions)
                return preview_board

            try:
                selected_move = player.module.select_move(
                    color,
                    board,
                    tuple(available_moves),
                    preview_move,
                )
            except Exception as exc:
                player_error = {
                    "player": player.name,
                    "player_id": player.id,
                    "turn": turn_number,
                    "type": "exception",
                    "message": str(exc),
                }
                ending_reason = "player_error"
                break

            if selected_move is not None and isinstance(selected_move, list):
                selected_move = tuple(selected_move)

            if selected_move is None:
                consecutive_passes += 1
                moves.append(
                    {
                        "turn": turn_number,
                        "color": COLOR_NAMES[color],
                        "player": player.name,
                        "move": None,
                        "captured": [],
                        "board": json_board(board),
                    }
                )
                if consecutive_passes >= 2:
                    ending_reason = "two_passes"
                    break
                continue

            if selected_move not in available_moves:
                player_error = {
                    "player": player.name,
                    "player_id": player.id,
                    "turn": turn_number,
                    "type": "illegal_move",
                    "message": f"Returned illegal move: {selected_move!r}",
                }
                ending_reason = "player_error"
                break

            board, captured = play_move(board, color, selected_move, previous_positions)
            previous_positions.add(board)
            captures[COLOR_NAMES[color]] += len(captured)
            consecutive_passes = 0
            moves.append(
                {
                    "turn": turn_number,
                    "color": COLOR_NAMES[color],
                    "player": player.name,
                    "move": json_move(selected_move),
                    "captured": [json_move(move) for move in captured],
                    "board": json_board(board),
                }
            )

        if ending_reason is None:
            ending_reason = "max_move_count_reached"

        score = score_area(board, komi)
        result_type = "scored"
        winner = score["winner"]

        if player_error is not None:
            result_type = "player_error_forfeit"
            error_color = None
            for color, player in players_by_color.items():
                if player.id == player_error["player_id"]:
                    error_color = color
                    break
            winner = WHITE if error_color == BLACK else BLACK

        if winner == BLACK:
            winner_name = black_player.name
        elif winner == WHITE:
            winner_name = white_player.name
        else:
            winner_name = None

        return {
            "game_id": game_id,
            "created_at": created_at,
            "board_size": self.size,
            "rule_set": "go-9x9-area-v1",
            "komi": float(komi),
            "maximum_move_count": int(max_move_count),
            "black_player": {
                "id": black_player.id,
                "name": black_player.name,
                "version": black_player.version,
            },
            "white_player": {
                "id": white_player.id,
                "name": white_player.name,
                "version": white_player.version,
            },
            "moves": moves,
            "passes": sum(1 for move in moves if move["move"] is None),
            "capture_counts": captures,
            "final_board": json_board(board),
            "final_scoring_ownership": json_board(score["ownership"]),
            "final_score": {
                "black": score["black"],
                "white": score["white"],
            },
            "winner": COLOR_NAMES[winner] if winner is not None else None,
            "winner_name": winner_name,
            "result_type": result_type,
            "ending_reason": ending_reason,
            "player_error": player_error,
        }
