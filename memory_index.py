import sqlite3, datetime, os

DB_PATH = os.path.join(os.path.dirname(__file__), ".xlink/memory.db")

class MemoryIndex:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.session_id = ""
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                msg_id TEXT UNIQUE,
                session_id TEXT,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                time_sort INTEGER
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                content, session_id, role,
                content=messages,
                tokenize='unicode61'
            );
            CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                INSERT INTO messages_fts(rowid, content, session_id, role)
                VALUES (new.id, new.content, new.session_id, new.role);
            END;
        """)
        self._conn.commit()

    def set_session(self, session_id):
        self.session_id = session_id

    def index_message(self, msg):
        now = datetime.datetime.now()
        time_sort = int(now.strftime("%Y%m%d"))
        try:
            self._conn.execute(
                "INSERT OR IGNORE INTO messages(msg_id, session_id, role, content, timestamp, time_sort) VALUES (?,?,?,?,?,?)",
                (msg.id, self.session_id, msg.role, msg.content, now.isoformat(), time_sort)
            )
            self._conn.commit()
        except sqlite3.OperationalError:
            pass

    def search(self, query, limit=5, days=30):
        cutoff = int((datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y%m%d"))
        rows = self._conn.execute(
            "SELECT m.msg_id, m.session_id, m.role, m.content, m.timestamp, m.time_sort, rank "
            "FROM messages_fts f JOIN messages m ON f.rowid = m.id "
            "WHERE messages_fts MATCH ? AND m.time_sort >= ? "
            "ORDER BY rank LIMIT 30",
            (query, cutoff)
        ).fetchall()
        today = datetime.datetime.now()
        scored = []
        for msg_id, session_id, role, content, timestamp, time_sort, rank in rows:
            days_ago = (today - datetime.datetime.strptime(timestamp[:10], "%Y-%m-%d")).days
            decay = 1.0 / (1.0 + days_ago * 0.1)
            score = rank * decay
            scored.append((score, msg_id, session_id, role, content[:500], timestamp))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[:limit]