
import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

DEFAULT_DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "simulation_local.db"
)


class LocalSimulationStore:
    """SQLite storage for local Simulation Engine development."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            str(self.db_path),
            timeout=10,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS simulation_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    case_data TEXT NOT NULL,
                    state_json TEXT NOT NULL DEFAULT '{}',
                    current_phase TEXT NOT NULL DEFAULT 'introduction',
                    is_paused INTEGER NOT NULL DEFAULT 0,
                    is_completed INTEGER NOT NULL DEFAULT 0,
                    diagnosis TEXT,
                    treatment_plan TEXT,
                    created_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    ),
                    updated_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    )
                );

                CREATE INDEX IF NOT EXISTS
                    ix_local_sim_sessions_user_created
                ON simulation_sessions(user_id, created_at);

                CREATE TABLE IF NOT EXISTS simulation_events (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT (
                        strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    ),
                    FOREIGN KEY(session_id)
                        REFERENCES simulation_sessions(id)
                        ON DELETE CASCADE,
                    UNIQUE(session_id, sequence_number)
                );

                CREATE INDEX IF NOT EXISTS
                    ix_local_sim_events_session_created
                ON simulation_events(session_id, created_at);
                """
            )

    def create_session(
        self,
        user_id: str,
        case_data: dict[str, Any],
        state: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> str:
        session_id = session_id or str(uuid4())

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO simulation_sessions (
                    id, user_id, case_data, state_json
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    user_id,
                    json.dumps(case_data),
                    json.dumps(state or {}),
                ),
            )

        return session_id

    def get_session(
        self,
        session_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM simulation_sessions
                WHERE id = ? AND user_id = ?
                """,
                (session_id, user_id),
            ).fetchone()

        if row is None:
            return None

        result = dict(row)
        result["case_data"] = json.loads(result["case_data"])
        result["state"] = json.loads(result.pop("state_json"))
        result["is_paused"] = bool(result["is_paused"])
        result["is_completed"] = bool(result["is_completed"])
        return result

    def save_state(
        self,
        session_id: str,
        user_id: str,
        state: dict[str, Any],
    ) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE simulation_sessions
                SET state_json = ?,
                    current_phase = ?,
                    is_paused = ?,
                    is_completed = ?,
                    diagnosis = ?,
                    treatment_plan = ?,
                    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                WHERE id = ? AND user_id = ?
                """,
                (
                    json.dumps(state),
                    state.get("current_phase", "introduction"),
                    int(bool(state.get("is_paused", False))),
                    int(bool(state.get("is_completed", False))),
                    state.get("diagnosis"),
                    state.get("treatment_plan"),
                    session_id,
                    user_id,
                ),
            )
            return cursor.rowcount == 1

    def append_event(
        self,
        session_id: str,
        user_id: str,
        event: dict[str, Any],
        sequence_number: int,
    ) -> str:
        event_id = str(event.get("event_id") or uuid4())

        with self._connect() as connection:
            owned_session = connection.execute(
                """
                SELECT 1
                FROM simulation_sessions
                WHERE id = ? AND user_id = ?
                """,
                (session_id, user_id),
            ).fetchone()

            if owned_session is None:
                raise ValueError("Simulation session not found")

            connection.execute(
                """
                INSERT INTO simulation_events (
                    id, session_id, sequence_number,
                    event_type, phase, details_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    session_id,
                    sequence_number,
                    event["event_type"],
                    event["phase"],
                    json.dumps(event.get("details", {})),
                ),
            )

        return event_id

    def list_events(
        self,
        session_id: str,
        user_id: str,
    ) -> list[dict[str, Any]] | None:
        with self._connect() as connection:
            owned_session = connection.execute(
                """
                SELECT 1
                FROM simulation_sessions
                WHERE id = ? AND user_id = ?
                """,
                (session_id, user_id),
            ).fetchone()

            if owned_session is None:
                return None

            rows = connection.execute(
                """
                SELECT *
                FROM simulation_events
                WHERE session_id = ?
                ORDER BY sequence_number
                """,
                (session_id,),
            ).fetchall()

        events = []
        for row in rows:
            event = dict(row)
            event["details"] = json.loads(
                event.pop("details_json")
            )
            events.append(event)

        return events
