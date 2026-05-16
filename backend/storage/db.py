"""SQLite-based session storage for interview Q&A history."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import aiosqlite

_DB_NAME = "sessions.db"


class SessionDB:
    """Async SQLite database for storing interview sessions and Q&A pairs."""

    def __init__(self, data_dir: Path):
        self._db_path = data_dir / _DB_NAME
        self._db: Optional[aiosqlite.Connection] = None

    async def init(self) -> None:
        """Open database and create tables if needed."""
        self._db = await aiosqlite.connect(str(self._db_path))
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                provider TEXT NOT NULL,
                interview_type TEXT DEFAULT 'technical',
                answer_mode TEXT DEFAULT 'detailed'
            );
            CREATE TABLE IF NOT EXISTS qa_pairs (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );
            """
        )
        await self._db.execute("PRAGMA foreign_keys = ON")
        await self._db.commit()

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    async def create_session(self, provider: str, interview_type: str = "technical", answer_mode: str = "detailed") -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "INSERT INTO sessions (id, started_at, provider, interview_type, answer_mode) VALUES (?, ?, ?, ?, ?)",
            (session_id, now, provider, interview_type, answer_mode),
        )
        await self._db.commit()
        return session_id

    async def end_session(self, session_id: str) -> None:
        """Mark a session as ended."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE sessions SET ended_at = ? WHERE id = ?",
            (now, session_id),
        )
        await self._db.commit()

    async def add_qa(self, session_id: str, question_id: str, question: str, answer: str) -> None:
        """Add a Q&A pair to a session."""
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "INSERT INTO qa_pairs (id, session_id, question, answer, timestamp) VALUES (?, ?, ?, ?, ?)",
            (question_id, session_id, question, answer, now),
        )
        await self._db.commit()

    async def list_sessions(self) -> list[dict]:
        """List all sessions with question counts, most recent first."""
        cursor = await self._db.execute(
            """
            SELECT s.id, s.started_at, s.ended_at, s.provider, s.interview_type, s.answer_mode,
                   COUNT(q.id) as question_count
            FROM sessions s
            LEFT JOIN qa_pairs q ON q.session_id = s.id
            GROUP BY s.id
            ORDER BY s.started_at DESC
            """
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get a session with all its Q&A pairs."""
        cursor = await self._db.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        )
        session = await cursor.fetchone()
        if not session:
            return None

        qa_cursor = await self._db.execute(
            "SELECT * FROM qa_pairs WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        qa_pairs = await qa_cursor.fetchall()

        result = dict(session)
        result["qa_pairs"] = [dict(row) for row in qa_pairs]
        return result

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and its Q&A pairs. Returns True if found."""
        cursor = await self._db.execute(
            "DELETE FROM sessions WHERE id = ?", (session_id,)
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def export_session_markdown(self, session_id: str) -> Optional[str]:
        """Export a session as Markdown."""
        session = await self.get_session(session_id)
        if not session:
            return None

        started = session["started_at"][:19].replace("T", " ")
        provider = session["provider"]
        lines = [
            f"# Interview Session — {started}",
            f"",
            f"**Provider:** {provider}  ",
            f"**Interview Type:** {session.get('interview_type', 'technical')}  ",
            f"**Answer Mode:** {session.get('answer_mode', 'detailed')}  ",
            f"**Questions:** {len(session['qa_pairs'])}",
            f"",
            "---",
            "",
        ]

        for i, qa in enumerate(session["qa_pairs"], 1):
            ts = qa["timestamp"][:19].replace("T", " ")
            lines.append(f"## Q{i}: {qa['question']}")
            lines.append(f"*{ts}*")
            lines.append("")
            lines.append(qa["answer"])
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    async def export_session_json(self, session_id: str) -> Optional[dict]:
        """Export a session as a JSON-serializable dict."""
        return await self.get_session(session_id)
