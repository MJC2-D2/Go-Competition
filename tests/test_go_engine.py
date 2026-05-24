import unittest

from backend.go_engine import BLACK, WHITE, legal_moves, new_board, play_move, score_area


class GoEngineTest(unittest.TestCase):
    def test_capture_removes_stone(self):
        board = new_board(3)
        previous = {board}
        board, _ = play_move(board, BLACK, (0, 1), previous)
        previous.add(board)
        board, _ = play_move(board, WHITE, (1, 1), previous)
        previous.add(board)
        board, _ = play_move(board, BLACK, (1, 0), previous)
        previous.add(board)
        board, _ = play_move(board, BLACK, (1, 2), previous)
        previous.add(board)
        board, captured = play_move(board, BLACK, (2, 1), previous)

        self.assertEqual(captured, [(1, 1)])
        self.assertEqual(board[1][1], 0)

    def test_suicide_is_not_legal(self):
        board = new_board(3)
        previous = {board}
        for move in ((0, 1), (1, 0), (1, 2), (2, 1)):
            board, _ = play_move(board, BLACK, move, previous)
            previous.add(board)

        self.assertNotIn((1, 1), legal_moves(board, WHITE, previous))

    def test_area_scoring_counts_stones_and_surrounded_empty_points(self):
        board = (
            (BLACK, BLACK, BLACK),
            (BLACK, 0, BLACK),
            (BLACK, BLACK, BLACK),
        )

        score = score_area(board, komi=0)

        self.assertEqual(score["black"], 9)
        self.assertEqual(score["white"], 0)
        self.assertEqual(score["winner"], BLACK)


if __name__ == "__main__":
    unittest.main()
