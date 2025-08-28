from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional

class Report:
    def __init__(self, bug_report: Optional[Any]):
        bug_description = bug_report.bug_description
        account_id = bug_report.report_user_id
        bug_id_number = bug_report.id

        self.timestamp: datetime = datetime.now(timezone.utc)
        self.bug_description: str = bug_description
        self.account_id: int = int(account_id)
        self.account_state: Optional[Dict[str, Any]] = None
        self.bug_id = bug_id_number

    def fetch_account_state(self,
                            db: Optional[Any] = None,
                            user_model: Optional[Any] = None,
                            raise_on_missing: bool = False) -> Dict[str, Any]:
        if callable(db) and user_model is None:
            try:
                result = db(self.account_id)
                if result is None:
                    if raise_on_missing:
                        raise ValueError(f"Account {self.account_id} not found by callable.")
                    self.account_state = {}
                else:
                    self.account_state = dict(result)
                return self.account_state
            except Exception as e:
                raise

        if db is not None and user_model is not None:
            try:
                user = None
                try:
                    user = user_model.query.get(self.account_id)
                except Exception:
                    user = None

                if user is None:
                    try:
                        session = getattr(db, "session", db)
                        user = session.query(user_model).get(self.account_id)
                    except Exception:
                        user = None

                if user is None:
                    if raise_on_missing:
                        raise ValueError(f"Account {self.account_id} not found in DB.")
                    self.account_state = {}
                    return self.account_state

                state = {}
                try:
                    table = getattr(user_model, "__table__", None)
                    if table is not None:
                        for col in table.columns:
                            state[col.name] = getattr(user, col.name)
                    else:
                        for k, v in vars(user).items():
                            if not k.startswith("_"):
                                state[k] = v
                except Exception:
                    for k, v in vars(user).items():
                        if not k.startswith("_"):
                            state[k] = v

                self.account_state = state
                return self.account_state
            except Exception as e:
                raise

        raise ValueError("fetch_account_state requires either a callable db or both (db, user_model).")

    def to_log_lines(self) -> list:
        timestamp = self.timestamp.isoformat(timespec='seconds')
        header = f"[{timestamp}] BUG REPORT (account_id={self.account_id}, bug_id={self.bug_id})"
        desc = f"Description: {self.bug_description}"
        
        account_json = json.dumps(self.account_state or {}, ensure_ascii=False)
        account_line = f"Account state: {account_json}"
        return [header, desc, account_line]
