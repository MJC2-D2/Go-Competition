import random


def name():
    return "Random Player"


def version():
    return "1.0"


def select_move(color, board, legal_moves, preview_move):
    if not legal_moves:
        return None
    return random.choice(legal_moves)
