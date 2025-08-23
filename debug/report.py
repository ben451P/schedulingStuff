from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional

class Report:
    """
    Holds all data for a bug report and can fetch the account state from the database.

    Usage patterns for fetch_account_state:
    - If you have a simple callable that returns a dict for an account:
          report.fetch_account_state(db_callable)
      where db_callable(account_id) -> dict

    - If you use Flask-SQLAlchemy or raw SQLAlchemy, pass (db, UserModel):
          report.fetch_account_state(db, UserModel)
      where `db` is the flask_sqlalchemy.SQLAlchemy instance (or a session-like object)
      and `UserModel` is your mapped user model class.
    """

    def __init__(self, bug_description: str, first_bug: bool, account_id: int):
        self.timestamp: datetime = datetime.now(timezone.utc)
        self.bug_description: str = bug_description
        self.first_bug: bool = bool(first_bug)
        self.account_id: int = int(account_id)
        self.account_state: Optional[Dict[str, Any]] = None  # populated by fetch_account_state

    def fetch_account_state(self,
                            db: Optional[Any] = None,
                            user_model: Optional[Any] = None,
                            raise_on_missing: bool = False) -> Dict[str, Any]:
        """
        Populate self.account_state.

        Parameters
        - db: either a callable (db_callable(account_id)->dict) OR a SQLAlchemy-like object
              (flask_sqlalchemy.SQLAlchemy instance or a session).
        - user_model: required if db is a SQLAlchemy object; the mapped model class for users.
        - raise_on_missing: if True, raises an exception when the account is not found.

        Returns:
            dict of account state (may be empty if not found).
        """
        # If user provided a callable (simple interface)
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

        # If using SQLAlchemy / Flask-SQLAlchemy
        if db is not None and user_model is not None:
            # Try common patterns: user_model.query.get(id) (Flask-SQLAlchemy)
            try:
                user = None
                # Flask-SQLAlchemy: user_model.query.get(...)
                try:
                    user = user_model.query.get(self.account_id)
                except Exception:
                    user = None

                # If above didn't work, try db.session.query
                if user is None:
                    try:
                        session = getattr(db, "session", db)  # db may be session or SQLAlchemy instance
                        user = session.query(user_model).get(self.account_id)
                    except Exception:
                        user = None

                if user is None:
                    if raise_on_missing:
                        raise ValueError(f"Account {self.account_id} not found in DB.")
                    self.account_state = {}
                    return self.account_state

                # Convert SQLAlchemy model instance to dict by iterating columns if possible
                state = {}
                try:
                    table = getattr(user_model, "__table__", None)
                    if table is not None:
                        for col in table.columns:
                            state[col.name] = getattr(user, col.name)
                    else:
                        # Fallback: copy attributes that don't start with _
                        for k, v in vars(user).items():
                            if not k.startswith("_"):
                                state[k] = v
                except Exception:
                    # Best-effort fallback
                    for k, v in vars(user).items():
                        if not k.startswith("_"):
                            state[k] = v

                self.account_state = state
                return self.account_state
            except Exception as e:
                raise

        raise ValueError("fetch_account_state requires either a callable db or both (db, user_model).")

    def to_log_lines(self) -> list:
        """
        Prepare one or more human-readable lines to be written to the log file.
        Returns a list of strings (one string per line).
        """
        timestamp = self.timestamp.isoformat(timespec='seconds')
        header = f"[{timestamp}] BUG REPORT (account_id={self.account_id})"
        desc = f"Description: {self.bug_description}"
        first_flag = f"First bug today: {self.first_bug}"
        # stringify account_state as pretty JSON (safe fallback to empty dict)
        account_json = json.dumps(self.account_state or {}, ensure_ascii=False)
        account_line = f"Account state: {account_json}"
        return [header, desc, first_flag, account_line]




# -------------------------
# Example usage (commented)
# -------------------------
# report = Report("Some page crashes when generating schedule", first_bug=True, account_id=123)
#
# # Option A: fetch account state with a callable
# def get_account_dict(account_id):
#     # return a dict representing account state (from DB)
#     return {"id": account_id, "email": "user@example.com", "role": "admin"}
#
# report.fetch_account_state(get_account_dict)
#
# # Option B: with Flask-SQLAlchemy
# # from your_app import db
# # from your_app.models import User
# # report.fetch_account_state(db, User)
#
# logger = Logger("log.txt")
# logger.write_report(report)
