import sqlite3
from contextlib import contextmanager

class Database:
    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    @contextmanager
    def get_connection(self):
        yield self.conn.cursor()
        self.conn.commit()
        return
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            case_id INTEGER PRIMARY KEY,
            case_type TEXT,
            status TEXT,
            reason TEXT,
            verdict TEXT,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            court_id INTEGER,
            og_message_id INTEGER,

            last_summary_index INTEGER DEFAULT 0,
            case_close_reason TEXT,
            case_closed_at TIMESTAMP,
                       
            FOREIGN KEY(court_id) REFERENCES courts(court_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS associated_cases (
            case_id INTEGER,
            associated_case_id INTEGER,
            PRIMARY KEY (case_id, associated_case_id),
            FOREIGN KEY(case_id) REFERENCES cases(case_id),
            FOREIGN KEY(associated_case_id) REFERENCES cases(case_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            case_id INTEGER,
            user_id INTEGER,
            role TEXT,
            PRIMARY KEY (case_id, user_id, role)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidences (
            evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id INTEGER,
            filename TEXT,
            summary TEXT,
            url TEXT,
            uploader_id INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(case_id) REFERENCES cases(case_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL,
            author_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            message_id INTEGER,
            message_reference_id INTEGER,
            summary TEXT,
            case_id INTEGER,
            speaker TEXT,
            is_judge INTEGER DEFAULT 0,
            FOREIGN KEY(case_id) REFERENCES cases(case_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS courts (
            court_id INTEGER PRIMARY KEY,
            name TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            guild_id INTEGER,
            channel_id INTEGER
        )
        """)

        self.conn.commit()
    
def get_database(db_path: str) -> Database:
    court_db = Database(db_path=db_path)
    return court_db