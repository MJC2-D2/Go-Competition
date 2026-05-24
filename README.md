# Go Competition

A local 9x9 Go competition app where Python player modules compete against each
other. The backend runs games, stores replays as JSON, and exposes an HTTP API.
The frontend is a React app for queueing matches, browsing history, replaying
games, and viewing the league table.

## Requirements

- Python 3.10 or newer
- Node.js and npm

The backend uses only the Python standard library. The frontend uses Vite,
React, and lucide-react.

## Project Layout

```text
backend/              Python game engine, runner, storage, API server
players/              Submitted player modules
examples/             Template/example player code
frontend/             React frontend
tests/                Backend unit tests
data/games/           Generated game replay files
project.md            Project design document
```

## Run The Backend

From the project root:

```bash
python3 -m backend.main
```

The API runs at:

```text
http://127.0.0.1:8000
```

Useful endpoints:

- `GET /api/players`
- `POST /api/matches`
- `GET /api/jobs`
- `GET /api/games`
- `GET /api/league`

## Run The Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Run Tests

From the project root:

```bash
python3 -m unittest
```

## Add A Player

Create a new `.py` file in `players/`. Each player must provide these functions:

```python
def name():
    return "My Player"


def version():
    return "1.0"


def select_move(color, board, legal_moves, preview_move):
    if not legal_moves:
        return None

    return legal_moves[0]
```

Rules for player code:

- `color` is `1` for white and `2` for black.
- `board` is an immutable tuple of tuples.
- Empty points are `0`, white stones are `1`, and black stones are `2`.
- Moves use zero-based `(row, col)` coordinates.
- Return `(row, col)` to play, or `None` to pass.
- Returning an illegal move, raising an exception, or returning malformed data
  forfeits the game as a player error.

See:

- `players/random_player.py`
- `players/first_capture_player.py`
- `examples/player_template.py`

## Current Rules

- 9x9 board.
- Black moves first.
- Captures use normal liberties.
- Suicide is illegal.
- Positional superko is enforced.
- The game ends after two consecutive passes.
- A configurable maximum move count is used as a fallback.
- Area scoring is used for the first version.
- Komi defaults to `6.5` and can be changed in the match setup form.

## Notes

Games are queued in the backend and run by a single background worker. Completed
games are stored as one JSON file per game under `data/games/`.
