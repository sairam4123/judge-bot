from enum import StrEnum

class CaseType(StrEnum):
    CRIMINAL = "Criminal"
    CIVIL = "Civil"
    FAMILY = "Family"
    TRAFFIC = "Traffic"
    SMALL_CLAIMS = "Small Claims"
    COUNTER_CASE = "Counter-case"

class CaseStatus(StrEnum):
    OPEN = "Open"
    CLOSED = "Closed"
    APPEALED = "Appealed"

class Case:
    def __init__(self, case_id: int, case_type: CaseType, status: CaseStatus, reason: str, participants: list[CaseParticipant], created_at: str = "", updated_at: str = "", court_id: int = 0, logs: list['LogEntry'] | None = None, verdict: str = "", summary: str = "", ):
        self.case_id = case_id
        self.case_type = case_type
        self.status = status
        self.reason = reason
        self.participants = participants
        self.verdict = verdict
        self.summary = summary
        self.logs: list[LogEntry] = logs if logs is not None else []
        self.created_at = created_at
        self.updated_at = updated_at
        self.court_id = court_id

    def to_dict(self, include_logs=False, include_participants=False) -> dict:
        return {
            "case_id": self.case_id,
            "case_type": self.case_type.value,
            "status": self.status.value,
            "reason": self.reason,
            "verdict": self.verdict,
            "summary": self.summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "court_id": self.court_id,
            } | ({
                "participants": [p.to_dict() for p in self.participants],
            } if include_participants else {}) | ({
                "logs": [log.to_dict() for log in self.logs],
            } if include_logs else {})
    
    @staticmethod
    def from_dict(data: dict) -> 'Case':
        return Case(
            case_id=data["case_id"],
            case_type=CaseType(data["case_type"]),
            status=CaseStatus(data["status"]),
            reason=data["reason"],
            participants=[CaseParticipant.from_dict(p) for p in data.get("participants", [])],
            verdict=data.get("verdict", ""),
            summary=data.get("summary", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            court_id=data.get("court_id", 0),
            logs=[LogEntry.from_dict(log) for log in data.get("logs", [])],
        )
    

    def add_log_entry(self, log_entry: 'LogEntry'):
        self.logs.append(log_entry)
    
class CaseRole(StrEnum):
    JUDGE = "Judge"
    PROSECUTOR = "Prosecutor"
    DEFENSE = "Defense"
    WITNESS = "Witness"

class CaseParticipant:
    def __init__(self, user_id: int, role: CaseRole):
        self.user_id = user_id
        self.role = role
    
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "role": self.role.value
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'CaseParticipant':
        return CaseParticipant(
            user_id=data["user_id"],
            role=CaseRole(data["role"])
        )

class LogEntry:
    def __init__(self, timestamp: str, author_id: int, content: str, message_id: int = 0, message_reference_id: int = 0, summary: str = ""):
        self.timestamp = timestamp
        self.author_id = author_id
        self.content = content
        self.message_id = message_id
        self.message_reference_id = message_reference_id
        self.summary = summary

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "author_id": self.author_id,
            "content": self.content,
            "message_id": self.message_id,
            "message_reference_id": self.message_reference_id,
            "summary": self.summary
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'LogEntry':
        return LogEntry(
            timestamp=data["timestamp"],
            author_id=data["author_id"],
            content=data["content"],
            message_id=data.get("message_id", 0),
            message_reference_id=data.get("message_reference_id", 0),
            summary=data.get("summary", "")
        )
    
    def summarize(self):
        raise NotImplementedError("LogEntry.summarize method is not implemented yet.")

class CourtDatabase:
    def __init__(self):
        self.cases: dict[int, Case] = {}
    
    def add_case(self, case: Case):
        self.cases[case.case_id] = case
    
    def get_case(self, case_id: int) -> Case | None:
        return self.cases.get(case_id)
    
    def close_case(self, case_id: int, verdict: str):
        case = self.get_case(case_id)
        if case:
            case.status = CaseStatus.CLOSED
            case.verdict = verdict
            self.cases[case_id] = case
    
    def list_open_cases(self) -> list[Case]:
        return [case for case in self.cases.values() if case.status == CaseStatus.OPEN]
    

def initialize_database() -> CourtDatabaseSqlite:
    court_db = CourtDatabase()
    db = CourtDatabaseSqlite(court_db=court_db)
    # Here you could load existing cases from a file or database
    return db

class CourtDatabaseSqlite:
    def __init__(self, court_db: CourtDatabase) -> None:
        self.court_db = court_db
        # Initialize SQLite connection here
        self.conn = None  # Placeholder for SQLite connection
    
    def connect(self, db_path: str) -> None:
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self) -> None:
        if self.conn is None:
            raise ValueError("Database connection is not established.")
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                case_id INTEGER PRIMARY KEY,
                case_type TEXT,
                status TEXT,
                reason TEXT,
                verdict TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_entries (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                timestamp TEXT,
                author_id INTEGER,
                is_judge INTEGER DEFAULT 0,
                content TEXT,
                message_id INTEGER,
                message_reference_id INTEGER,
                summary TEXT,
                FOREIGN KEY(case_id) REFERENCES cases(case_id),
                FOREIGN KEY(author_id) REFERENCES participants(user_id)
            );
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                case_id INTEGER,
                user_id INTEGER,
                role TEXT,
                PRIMARY KEY (case_id, user_id, role),
                FOREIGN KEY(case_id) REFERENCES cases(case_id)
            );
        ''')



        self.conn.commit()