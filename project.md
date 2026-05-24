# Go Game Design

This project creates a competitive arena where submitted Python programs
("players") compete at the game Go. The first version uses a simplified 9x9
board and focuses on being easy to understand, easy to extend, and useful as a
learning environment.

## Goals

- Allow trusted people to submit Python player code.
- Run matches between two selected players.
- Store completed games so they can be replayed later.
- Provide a React frontend for running games, browsing history, replaying moves,
  and viewing league standings.
- Provide a simple player API that is approachable for people new to Python.

## System Design

### Backend Runtime

The backend is implemented in Python.

It is responsible for:

- Loading available player modules from a known players directory.
- Running games between selected players.
- Enforcing the Go rules.
- Detecting invalid player behaviour.
- Writing completed game records to files.
- Serving game history, replay data, player lists, and league statistics to the
  frontend.

Submitted player code is trusted code from trusted people, so the first version
may run player code directly in the backend process. Even so, the backend should
still treat player errors as game events and record them clearly.

Recommended backend structure:

- `go_engine/` - board state, legal moves, captures, ko/superko, scoring.
- `players/` - submitted player modules.
- `runner/` - game loop and match execution.
- `storage/` - reading and writing game files.
- `api/` - HTTP API used by the React frontend.
- `examples/` - example players and learning material.

### Frontend

The frontend is implemented in React.

It should provide these main views:

- Run match.
- Game history.
- Replay viewer.
- League table.
- Player list.

In the run match view, the user can:

- Select the black player.
- Select the white player.
- Select how many games to run.
- Set the komi, defaulting to `6.5`.
- Allow the same player code to be selected for both colours.
- Run multiple games with colours alternating between games.

Games should be queued to run in the background. The first version should use a
single-worker queue so only one game runs at any given time. This keeps the
runtime easier to reason about and avoids concurrent access issues with player
modules and file storage.

The replay viewer should:

- Show the board at each move.
- Show final scoring ownership after scoring.
- Step forward and backward through the game.
- Provide a slider to jump to any move.
- Show the players, result, score, and any player error.

The game history view should:

- List stored games with the most recent games first.
- Filter by player name.
- Open a selected game in the replay viewer.

The league table should:

- List all players.
- Be reorderable by each metric.
- Include wins, losses, draws, win rate, points, rating, average margin, illegal
  move count, timeout count, crash count, and player error count.

## Rules

### Board

- The board is 9x9.
- Coordinates are zero-based Python indexes.
- Coordinates are represented as `(row, col)`.
- `row` and `col` are integers from `0` to `8`.
- The top-left point is `(0, 0)`.

The board is represented as a matrix:

- `0` means empty.
- `1` means white stone.
- `2` means black stone.

### Turns

- Black plays first.
- Players alternate turns.
- A player may play a legal move or pass.
- The game ends after two consecutive passes.
- A configurable maximum move count is used as a safety fallback. The
  recommended default for 9x9 is `250` turns.

If the maximum move count is reached before two consecutive passes, the game
ends immediately, is scored from the current board position, and the result is
recorded with a `max_move_count_reached` ending reason.

### Captures

A group is a set of connected stones of the same colour. Stones are connected
orthogonally, not diagonally.

A group is captured when it has no liberties. A liberty is an empty point
orthogonally adjacent to any stone in the group.

When a player places a stone, any adjacent opponent groups with no liberties are
removed from the board.

### Suicide

Suicide is illegal.

A player may not place a stone if their own group would have no liberties after
the move, unless that move captures at least one opposing group and therefore
creates a liberty.

### Superko

The game uses positional superko.

A move is illegal if it would recreate any previous whole-board position from
the same game. This prevents immediate ko recapture and longer repeated cycles.

Passes do not change the board position.

### Scoring

The first version uses area scoring because it is deterministic and easier to
automate than territory scoring with dead-stone judgement.

At the end of the game:

- Each player receives one point for each of their stones still on the board.
- Each player receives one point for each empty point surrounded only by their
  stones.
- Neutral points do not count for either player.
- Captured stones do not count directly as prisoners. They matter because they
  have been removed from the board and may change the final area.
- Dead stones are not judged separately in the first version. If a player wants
  opposing stones removed before scoring, they must capture them before the game
  ends.
- Komi is configurable in the game setup view.
- The default komi is `6.5` points for white.

With a fractional komi such as `6.5`, a tie is not possible because the final
scores cannot be equal. A tie is only possible if the competition is configured
with no komi or an integer komi and both players finish with the same score.

The backend should store final scoring ownership in the completed game record so
the frontend can display the final scoring result.

### Result Types

A game can end with:

- Black win.
- White win.
- Draw, only when the scoring configuration allows it.
- Player error forfeit.

## Player Code

Player code is implemented as a Python module placed in the known players
directory.

Each player module should provide:

```python
def name():
    return "My Player"


def version():
    return "1.0"


def select_move(color, board, legal_moves, preview_move):
    ...
```

This deliberately uses simple Python functions rather than classes, because that
is easier for new Python programmers to understand.

### Player API

`name()`

Returns the display name of the player.

`version()`

Returns the version number of the player. This should be changed whenever the
player logic changes.

`select_move(color, board, legal_moves, preview_move)`

Called once for each turn.

Arguments:

- `color`: the colour being played by this player. This is `1` for white or `2`
  for black.
- `board`: the current board as an immutable matrix from the player's point of
  view.
- `legal_moves`: a list of legal moves. Each move is a `(row, col)` tuple.
- `preview_move`: a helper function that returns the board that would result
  from making a given legal move.

Return value:

- Return `(row, col)` to play a move.
- Return `None` to pass.

The player only receives the current board state. It does not receive the full
move history, capture history, score estimate, or opponent metadata.

The backend should ensure that the board passed to a player cannot be mutated by
that player. A tuple of tuples is a good representation for this:

```python
board = (
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0, 0),
)
```

### Helper Function

The backend provides a helper function called `preview_move` that lets a player
preview a move.

The helper takes a move coordinate and returns the resulting board state as if
the player had made that move:

```python
new_board = preview_move((3, 4))
```

Calling the helper does not count as the player's turn.

Helper calls should still be part of the player's turn execution, so excessive
or broken helper use can still cause the player's turn to fail if the backend
later adds time limits.

### Example Random Player

This player chooses a random legal move. If there are no legal moves, it passes.

```python
import random


def name():
    return "Random Player"


def version():
    return "1.0"


def select_move(color, board, legal_moves, preview_move):
    if not legal_moves:
        return None

    return random.choice(legal_moves)
```

## Player Errors

If a player behaves incorrectly, their current turn is void and they immediately
forfeit the game.

This should be recorded as a player error.

Player errors include:

- Returning an illegal move.
- Returning malformed data.
- Raising an exception.
- Failing to provide the required functions.
- Returning a duplicate or invalid player name.
- Mutating data if mutable data is ever accidentally exposed.
- Timing out, if time limits are added later.

The stored game record should include:

- Which player caused the error.
- Which turn caused the error.
- The error type.
- A short error message.
- The final result.

## Game Storage

Completed games are stored as files for persistence.

This is acceptable for the first version, but the design should assume thousands
of games. Use one structured file per game rather than appending all games to a
single file.

Recommended format: JSON.

Recommended directory layout:

```text
data/
  games/
    2026/
      05/
        2026-05-24T153000Z-game-id.json
```

Each game file should include:

- Game ID.
- Created timestamp.
- Board size.
- Rule set name/version.
- Komi.
- Maximum move count.
- Black player name.
- Black player version.
- White player name.
- White player version.
- Move list.
- Passes.
- Capture counts.
- Final board.
- Final scoring ownership.
- Final score.
- Winner.
- Result type.
- Ending reason, such as `two_passes`, `player_error`, or
  `max_move_count_reached`.
- Player error details, if any.

For thousands of games, maintain a lightweight index file or generated cache for
the game list and league table. This avoids reading every full replay file on
every frontend request.

## Competition And League Table

When running multiple games between two players, colours should alternate:

- Game 1: selected black player plays black.
- Game 2: selected black player plays white.
- Game 3: selected black player plays black again.
- Continue alternating.

The league table should include:

| Metric | Meaning |
| --- | --- |
| Games | Total completed games |
| Wins | Games won |
| Losses | Games lost |
| Draws | Games drawn |
| Win rate | Wins divided by completed games |
| Points | Competition points, for example 3 for win, 1 for draw, 0 for loss |
| Rating | Elo rating |
| Average margin | Average score difference in completed games |
| Illegal moves | Number of forfeits caused by illegal moves |
| Timeouts | Number of forfeits caused by timeout, if time limits are added |
| Crashes | Number of forfeits caused by exceptions |
| Player errors | Total player-error forfeits |

The table should be reorderable by any metric.

Elo should be used for the first version of ratings. More advanced systems such
as Glicko can be considered later if rating confidence becomes important.

## Learning Environment

The project should include a small player development kit:

- A documented player template.
- The random player example.
- At least one slightly smarter example player.
- A local command for testing one player against another.
- Clear error messages when player code fails.
- Documentation explaining the board format, coordinates, return values, and
  common mistakes.

## Settled Design Decisions

- Komi is configured in the game setup view and defaults to `6.5`.
- Scoring uses area scoring in the first version.
- Final scoring ownership is displayed in the frontend.
- Player ratings use Elo in the first version.
- Games run through a background queue with a single active game worker.
- A maximum move count is included as a safety fallback.
