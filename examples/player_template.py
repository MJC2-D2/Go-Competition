class Player:
    def name(self):
        return "My Player"

    def version(self):
        return "1.0"

    def select_move(self, color, board, preview_move, get_legal_moves):
        legal_moves = get_legal_moves(color, board)
        if not legal_moves:
            return None

        # Replace this with your own strategy.
        return legal_moves[0]
