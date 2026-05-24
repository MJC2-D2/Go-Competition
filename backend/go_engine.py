from collections import deque

EMPTY = 0
WHITE = 1
BLACK = 2


def opponent(color):
    return WHITE if color == BLACK else BLACK


def new_board(size=9):
    return tuple(tuple(EMPTY for _ in range(size)) for _ in range(size))


def board_size(board):
    return len(board)


def on_board(board, row, col):
    size = board_size(board)
    return 0 <= row < size and 0 <= col < size


def neighbors(board, row, col):
    for next_row, next_col in (
        (row - 1, col),
        (row + 1, col),
        (row, col - 1),
        (row, col + 1),
    ):
        if on_board(board, next_row, next_col):
            yield next_row, next_col


def set_point(board, row, col, value):
    rows = [list(board_row) for board_row in board]
    rows[row][col] = value
    return tuple(tuple(board_row) for board_row in rows)


def remove_points(board, points):
    rows = [list(board_row) for board_row in board]
    for row, col in points:
        rows[row][col] = EMPTY
    return tuple(tuple(board_row) for board_row in rows)


def collect_group(board, start):
    color = board[start[0]][start[1]]
    if color == EMPTY:
        return set()

    group = set()
    pending = deque([start])

    while pending:
        point = pending.popleft()
        if point in group:
            continue
        group.add(point)

        for adjacent in neighbors(board, point[0], point[1]):
            row, col = adjacent
            if board[row][col] == color and adjacent not in group:
                pending.append(adjacent)

    return group


def count_liberties(board, group):
    liberties = set()
    for row, col in group:
        for next_row, next_col in neighbors(board, row, col):
            if board[next_row][next_col] == EMPTY:
                liberties.add((next_row, next_col))
    return len(liberties)


def play_move(board, color, move, previous_positions):
    if move is None:
        return board, []

    if not isinstance(move, tuple) or len(move) != 2:
        raise ValueError("Move must be a (row, col) tuple or None.")

    row, col = move
    if not isinstance(row, int) or not isinstance(col, int):
        raise ValueError("Move coordinates must be integers.")
    if not on_board(board, row, col):
        raise ValueError("Move is outside the board.")
    if board[row][col] != EMPTY:
        raise ValueError("Move point is already occupied.")

    next_board = set_point(board, row, col, color)
    captured = []

    for next_row, next_col in neighbors(next_board, row, col):
        if next_board[next_row][next_col] != opponent(color):
            continue
        group = collect_group(next_board, (next_row, next_col))
        if count_liberties(next_board, group) == 0:
            captured.extend(sorted(group))
            next_board = remove_points(next_board, group)

    own_group = collect_group(next_board, (row, col))
    if count_liberties(next_board, own_group) == 0:
        raise ValueError("Suicide is illegal.")

    if next_board in previous_positions:
        raise ValueError("Move violates positional superko.")

    return next_board, captured


def legal_moves(board, color, previous_positions):
    moves = []
    for row in range(board_size(board)):
        for col in range(board_size(board)):
            if board[row][col] != EMPTY:
                continue
            try:
                play_move(board, color, (row, col), previous_positions)
            except ValueError:
                continue
            moves.append((row, col))
    return moves


def score_area(board, komi):
    black_score = 0.0
    white_score = float(komi)
    ownership = [[EMPTY for _ in board] for _ in board]
    visited_empty = set()

    for row, board_row in enumerate(board):
        for col, value in enumerate(board_row):
            if value == BLACK:
                black_score += 1
                ownership[row][col] = BLACK
            elif value == WHITE:
                white_score += 1
                ownership[row][col] = WHITE

    for row, board_row in enumerate(board):
        for col, value in enumerate(board_row):
            point = (row, col)
            if value != EMPTY or point in visited_empty:
                continue

            region = set()
            adjacent_colors = set()
            pending = deque([point])

            while pending:
                current = pending.popleft()
                if current in region:
                    continue
                region.add(current)
                visited_empty.add(current)

                for next_row, next_col in neighbors(board, current[0], current[1]):
                    next_value = board[next_row][next_col]
                    if next_value == EMPTY and (next_row, next_col) not in region:
                        pending.append((next_row, next_col))
                    elif next_value in (WHITE, BLACK):
                        adjacent_colors.add(next_value)

            if len(adjacent_colors) == 1:
                owner = next(iter(adjacent_colors))
                if owner == BLACK:
                    black_score += len(region)
                else:
                    white_score += len(region)
                for owned_row, owned_col in region:
                    ownership[owned_row][owned_col] = owner

    if black_score > white_score:
        winner = BLACK
    elif white_score > black_score:
        winner = WHITE
    else:
        winner = None

    return {
        "black": black_score,
        "white": white_score,
        "winner": winner,
        "ownership": tuple(tuple(row) for row in ownership),
    }
