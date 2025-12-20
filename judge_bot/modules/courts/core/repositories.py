from judge_bot.bot import JudgeBot
from judge_bot.modules.courts.core.models import Case, LogEntry, Evidence, Court, CaseParticipant

class CaseRepository:
    def __init__(self, bot: 'JudgeBot'):
        self.bot = bot
    
    def create_case(self, case: Case):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO cases (case_id, case_type, status, reason, verdict, summary, court_id, og_message_id)"
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (case.case_id, case.type, case.status, case.reason, case.verdict, case.summary, case.court_id, case.og_message_id)
            )
    
    def list_cases(self) -> list[Case]:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM cases")
            rows = cursor.fetchall()
            cases = []
            for row in rows:
                case = Case(
                    case_id=row[0],
                    type=row[1],
                    status=row[2],
                    reason=row[3],
                    verdict=row[4],
                    summary=row[5],
                    court_id=row[6],
                    og_message_id=row[7],
                    created_at=row[8],
                    updated_at=row[9]
                )
                cases.append(case)
            return cases
    
    def update_summary(self, case_id: int, summary: str, last_summary_index: int):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "UPDATE cases SET summary = ?, last_summary_index = ?, updated_at = CURRENT_TIMESTAMP WHERE case_id = ?",
                (summary, last_summary_index, case_id)
            )

    def get_case(self, case_id: int) -> Case | None:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
            row = cursor.fetchone()
            if not row:
                return None
            print(row)
            case = Case(
                case_id=row[0],
                type=row[1],
                status=row[2],
                reason=row[3],
                verdict=row[4],
                summary=row[5],
                created_at=row[6],
                updated_at=row[7],
                court_id=row[8],
                og_message_id=row[9],
                last_summary_index=row[10],
                case_close_reason=row[11],
                case_closed_at=row[12],
            )
            return case
    
    def has_case(self, case_id: int) -> bool:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT 1 FROM cases WHERE case_id = ?", (case_id,))
            row = cursor.fetchone()
            return row is not None
    
    def close_case(self, case_id: int, verdict: str):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "UPDATE cases SET status = ?, verdict = ?, updated_at = CURRENT_TIMESTAMP WHERE case_id = ?",
                ("closed", verdict, case_id)
            )
    
    def reopen_case(self, case_id: int):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "UPDATE cases SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE case_id = ?",
                ("open", case_id)
            )
    
    def get_accused(self, case_id: int) -> list[int]:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT user_id FROM participants WHERE case_id = ? AND role = 'accused'",
                (case_id,)
            )
            row = cursor.fetchall()
            return [r[0] for r in row]
    
    def get_accuser(self, case_id: int) -> int | None:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT user_id FROM participants WHERE case_id = ? AND role = 'accuser'",
                (case_id,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
        
    def update_og_message_id(self, case_id: int, og_message_id: int):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "UPDATE cases SET og_message_id = ?, updated_at = CURRENT_TIMESTAMP WHERE case_id = ?",
                (og_message_id, case_id)
            )
    
    def update_case(self, case_id: int, *, case_type: str | None = None, reason: str | None = None, accused: list[int] | None = None):
        with self.bot.db.get_connection() as conn:
            if case_type is not None:
                conn.execute(
                    "UPDATE cases SET case_type = ?, updated_at = CURRENT_TIMESTAMP WHERE case_id = ?",
                    (case_type, case_id)
                )
            if reason is not None:
                conn.execute(
                    "UPDATE cases SET reason = ?, updated_at = CURRENT_TIMESTAMP WHERE case_id = ?",
                    (reason, case_id)
                )
            if accused is not None:
                # First, remove existing accused participants
                conn.execute(
                    "DELETE FROM participants WHERE case_id = ? AND role = 'accused'",
                    (case_id,)
                )
                # Then, add the new accused participants
                for user_id in accused:
                    conn.execute(
                        "INSERT INTO participants (case_id, user_id, role) VALUES (?, ?, 'accused')",
                        (case_id, user_id)
                    )
        
    def update_verdict(self, case_id: int, verdict: str):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "UPDATE cases SET verdict = ?, updated_at = CURRENT_TIMESTAMP WHERE case_id = ?",
                (verdict, case_id)
            )

class LogRepository:
    def __init__(self, bot: 'JudgeBot'):
        self.bot = bot
    
    def add_log(self, case_id: int, log_entry: LogEntry):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO log_entries (case_id, timestamp, author_id, is_judge, content, message_id, message_reference_id, summary, speaker) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (case_id, log_entry.timestamp, log_entry.author_id, int(log_entry.is_judge), log_entry.message, log_entry.message_id, log_entry.message_reference_id, log_entry.summary, log_entry.speaker)
            )
    
    def get_logs(self, case_id: int) -> list[LogEntry]:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM log_entries WHERE case_id = ?", (case_id,))
            rows = cursor.fetchall()
            logs = []
            for row in rows:
                log_entry = LogEntry(
                    timestamp=row[1],
                    author_id=row[2],
                    message=row[3],
                    message_id=row[4],
                    message_reference_id=row[5],
                    summary=row[6],
                    speaker=row[8],
                    is_judge=bool(row[7]),
                )
                logs.append(log_entry)
            return logs
    
    def count_logs(self, case_id: int) -> int:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(message_id) FROM log_entries WHERE case_id = ?", (case_id,))
            row = cursor.fetchone()
            return row[0] if row else 0

class EvidenceRepository:
    def __init__(self, bot: 'JudgeBot'):
        self.bot = bot
    
    def add_evidence(self, evidence: Evidence):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO evidences (case_id, filename, url, summary, uploader_id, created_at, description) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (evidence.case_id, evidence.filename, evidence.url, evidence.summary, evidence.uploader_id, evidence.created_at, evidence.description)
            )
    
    def get_evidences(self, case_id: int) -> list[Evidence]:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM evidences WHERE case_id = ?", (case_id,))
            rows = cursor.fetchall()
            evidences = []
            for row in rows:
                evidence = Evidence(
                    evidence_id=row[0],
                    case_id=row[1],
                    filename=row[2],
                    summary=row[3],
                    url=row[4],
                    uploader_id=row[5],
                    description=row[6],
                    created_at=row[7]
                )
                evidences.append(evidence)
            return evidences
    
class CourtRepository:
    def __init__(self, bot: 'JudgeBot'):
        self.bot = bot
    def create_court(self, court: Court):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO courts (court_id, name, description, guild_id, channel_id) "
                "VALUES (?, ?, ?, ?, ?)",
                (court.court_id, court.name, court.description, court.guild_id, court.channel_id)
            )
    def get_court(self, court_id: int) -> Court | None:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM courts WHERE court_id = ?", (court_id,))
            row = cursor.fetchone()
            if not row:
                return None
            court = Court(
                court_id=row[0],
                name=row[1],
                description=row[2],
                created_at=row[3],
                guild_id=row[4],
                channel_id=row[5],
            )
            return court
    
    def has_court(self, court_id: int) -> bool:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT 1 FROM courts WHERE court_id = ?", (court_id,))
            row = cursor.fetchone()
            return row is not None
    
    def contains_court(self, guild_id: int, channel_id: int) -> bool:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT 1 FROM courts WHERE guild_id = ? AND channel_id = ?", (guild_id, channel_id))
            row = cursor.fetchone()
            return row is not None

    def list_courts(self) -> list:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM courts")
            rows = cursor.fetchall()
            courts = []
            for row in rows:
                court = Court(
                    court_id=row[0],
                    name=row[1],
                    description=row[2],
                    created_at=row[3],
                    guild_id=row[4],
                    channel_id=row[5],
                )
                courts.append(court)
            return courts
    
    def delete_court(self, court_id: int):
        with self.bot.db.get_connection() as conn:
            conn.execute("DELETE FROM courts WHERE court_id = ?", (court_id,))

class CaseParticipantRepository:
    def __init__(self, bot: 'JudgeBot'):
        self.bot = bot
    
    def add_participant(self, case_id: int, participant: CaseParticipant):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO participants (case_id, user_id, role) "
                "VALUES (?, ?, ?)",
                (case_id, participant.user_id, participant.role)
            )
    
    def add_accused_participants(self, case_id: int, accused_user_ids: list[int]):
        with self.bot.db.get_connection() as conn:
            for user_id in accused_user_ids:
                conn.execute(
                    "INSERT INTO participants (case_id, user_id, role) "
                    "VALUES (?, ?, 'accused')",
                    (case_id, user_id)
                )
    
    def add_accuser_participant(self, case_id: int, accuser_user_id: int):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO participants (case_id, user_id, role) "
                "VALUES (?, ?, 'accuser')",
                (case_id, accuser_user_id)
            )
    
    def get_participants(self, case_id: int) -> list:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM participants WHERE case_id = ?", (case_id,))
            rows = cursor.fetchall()
            participants = []
            for row in rows:
                participant = CaseParticipant(
                    user_id=row[1],
                    role=row[2]
                )
                participants.append(participant)
            return participants
    
    def add_witness_participant(self, case_id: int, witness_user_id: int):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO participants (case_id, user_id, role) "
                "VALUES (?, ?, 'witness')",
                (case_id, witness_user_id)
            )

class AssociatedCaseRepository:
    def __init__(self, bot: 'JudgeBot'):
        self.bot = bot
    
    def add_associated_case(self, case_id: int, associated_case_id: int):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "INSERT INTO associated_cases (case_id, associated_case_id) "
                "VALUES (?, ?)",
                (case_id, associated_case_id)
            )
    
    def link_associated_cases(self, case_id: int, associated_case_ids: list[int]):
        with self.bot.db.get_connection() as conn:
            conn.execute(
                "DELETE FROM associated_cases WHERE case_id = ?",
                (case_id,)
            )
            for associated_case_id in associated_case_ids:
                conn.execute(
                    "INSERT INTO associated_cases (case_id, associated_case_id) "
                    "VALUES (?, ?)",
                    (case_id, associated_case_id)
                )
    
    def get_associated_cases(self, case_id: int) -> list:
        with self.bot.db.get_connection() as conn:
            cursor = conn.execute("SELECT associated_case_id FROM associated_cases WHERE case_id = ?", (case_id,))
            rows = cursor.fetchall()
            associated_case_ids = [row[0] for row in rows]
            return associated_case_ids

class RepositoryManager:
    def __init__(self, bot: 'JudgeBot'):
        self.cases = CaseRepository(bot)
        self.logs = LogRepository(bot)
        self.evidences = EvidenceRepository(bot)
        self.courts = CourtRepository(bot)
        self.associated_cases = AssociatedCaseRepository(bot)
        self.participants = CaseParticipantRepository(bot)
    