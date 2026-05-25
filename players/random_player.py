import random


class Player:
    # count the number of moves that have been called for this player
    def __init__(self):
        self.move_count = 0

    def name(self):
        return "Random Player"

    def version(self):
        return "1.1"

    def select_move(self, color, board, preview_move, get_legal_moves):
        opponent = 1 if color == 2 else 2

        # If the opponent has no legal moves, we can pass and win immediately.
        if not get_legal_moves(opponent, board):
            return None

        # Otherwise, select a random legal move.
        legal_moves = get_legal_moves(color, board)
        if not legal_moves:
            return None
        
        self.move_count += 1
        return random.choice(legal_moves)
