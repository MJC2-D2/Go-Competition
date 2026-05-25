class Player:
    def name(self):
        return "Tactical Pressure Player"

    def version(self):
        return "1.0"

    def select_move(self, color, board, preview_move, get_legal_moves):
        opponent = 1 if color == 2 else 2
        legal_moves = get_legal_moves(color, board)
        if not legal_moves:
            return None

        size = len(board)
        center = (size - 1) / 2.0
        board_own_count = count_color(board, color)
        board_opp_count = count_color(board, opponent)

        best_move = None
        best_score = None

        for move in legal_moves:
            next_board = preview_move(color, board, move)

            own_gain = count_color(next_board, color) - board_own_count
            opp_loss = board_opp_count - count_color(next_board, opponent)

            own_group = collect_group(next_board, move)
            own_liberties = count_liberties(next_board, own_group)

            score = 0.0

            # Captures are the strongest local tactical signal.
            score += opp_loss * 30.0

            # Prefer healthy groups and avoid one-liberty self-atari shapes.
            score += own_liberties * 3.0
            if own_liberties == 1 and opp_loss == 0:
                score -= 40.0

            # Larger secure group growth is usually better than tiny additions.
            score += max(0, own_gain - 1) * 2.5

            # Encourage local pressure around adjacent enemy groups.
            score += adjacent_attack_pressure(next_board, move, opponent)

            # Prefer central development in the opening and midgame.
            distance = abs(move[0] - center) + abs(move[1] - center)
            score += max(0.0, 8.0 - distance) * 0.3

            # Avoid filling likely own eyes unless it captures.
            if opp_loss == 0 and looks_like_own_eye(board, move, color):
                score -= 15.0

            if best_score is None or score > best_score:
                best_score = score
                best_move = move

        return best_move


def count_color(board, color):
    return sum(point == color for row in board for point in row)


def adjacent_attack_pressure(board, move, opponent):
    pressure = 0.0
    seen_groups = set()

    for point in neighbors(board, move[0], move[1]):
        row, col = point
        if board[row][col] != opponent or point in seen_groups:
            continue

        group = collect_group(board, point)
        seen_groups.update(group)
        liberties = count_liberties(board, group)

        if liberties == 1:
            pressure += 14.0 + len(group) * 1.5
        elif liberties == 2:
            pressure += 5.0 + len(group) * 0.5

    return pressure


def looks_like_own_eye(board, move, color):
    row, col = move
    adjacent = list(neighbors(board, row, col))
    if not adjacent:
        return False
    return all(board[next_row][next_col] == color for next_row, next_col in adjacent)


def on_board(board, row, col):
    size = len(board)
    return 0 <= row < size and 0 <= col < size


def neighbors(board, row, col):
    candidates = (
        (row - 1, col),
        (row + 1, col),
        (row, col - 1),
        (row, col + 1),
    )
    for next_row, next_col in candidates:
        if on_board(board, next_row, next_col):
            yield next_row, next_col


def collect_group(board, start):
    color = board[start[0]][start[1]]
    if color == 0:
        return set()

    group = set()
    pending = [start]

    while pending:
        point = pending.pop()
        if point in group:
            continue

        group.add(point)
        row, col = point
        for next_row, next_col in neighbors(board, row, col):
            if board[next_row][next_col] == color and (next_row, next_col) not in group:
                pending.append((next_row, next_col))

    return group


def count_liberties(board, group):
    liberties = set()
    for row, col in group:
        for next_row, next_col in neighbors(board, row, col):
            if board[next_row][next_col] == 0:
                liberties.add((next_row, next_col))
    return len(liberties)
