import random


def name():
    return "Random Player"


def version():
    return "1.1"


def select_move(color, board, preview_move, get_legal_moves):
    opponent = 1 if color == 2 else 2

    # If the opponent has no legal moves, we can pass and win immediately.
    if not get_legal_moves(opponent, board):
        return None

    # Otherwise, select a random legal move.
    legal_moves = get_legal_moves(color, board)
    if not legal_moves:
        return None
    return random.choice(legal_moves)
