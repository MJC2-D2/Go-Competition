def name():
    return "My Player"


def version():
    return "1.0"


def select_move(color, board, preview_move, get_legal_moves):
    legal_moves = get_legal_moves(color, board)
    if not legal_moves:
        return None

    # Replace this with your own strategy.
    return legal_moves[0]
