def name():
    return "First Capture Player"


def version():
    return "1.0"


def select_move(color, board, preview_move, get_legal_moves):
    opponent = 1 if color == 2 else 2
    legal_moves = get_legal_moves(color, board)

    for move in legal_moves:
        next_board = preview_move(color, board, move)
        if count_color(next_board, opponent) < count_color(board, opponent):
            return move

    if legal_moves:
        return legal_moves[0]

    return None


def count_color(board, color):
    return sum(point == color for row in board for point in row)
