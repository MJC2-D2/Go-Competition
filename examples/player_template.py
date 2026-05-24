def name():
    return "My Player"


def version():
    return "1.0"


def select_move(color, board, legal_moves, preview_move):
    if not legal_moves:
        return None

    # Replace this with your own strategy.
    return legal_moves[0]
