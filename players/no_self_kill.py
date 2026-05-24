def name():
    return "First Capture Player"


def version():
    return "1.0"


def select_move(color, board, legal_moves, preview_move):
    opponent = 1 if color == 2 else 2

    my_moves = legal_moves[]

    for move in legal_moves:
        next_board = preview_move(move)
        if count_color(next_board, color) < count_color(board, color):
            pass
        else count_color(next_board, opponent) < count_color(board, opponent):
            return move

    if legal_moves:
        return legal_moves[0]

    return None


def count_color(board, color):
    return sum(point == color for row in board for point in row)
