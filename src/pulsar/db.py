from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,
  payload TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  backend TEXT NOT NULL,
  request TEXT NOT NULL,
  response TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS factors (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  family TEXT NOT NULL,
  spec TEXT NOT NULL,
  created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS hypotheses (
  id TEXT PRIMARY KEY,
  factor_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evaluations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  factor_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  metrics TEXT NOT NULL,
  passed INTEGER NOT NULL,
  created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS promotions (
  factor_id TEXT PRIMARY KEY,
  state TEXT NOT NULL,
  reason TEXT NOT NULL,
  updated TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  factor_id TEXT,
  title TEXT NOT NULL,
  reason TEXT NOT NULL,
  created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  market_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  quantity REAL NOT NULL,
  price REAL NOT NULL,
  fee REAL NOT NULL,
  mode TEXT NOT NULL,
  factor_id TEXT,
  ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS risk_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  book TEXT NOT NULL,
  kind TEXT NOT NULL,
  detail TEXT NOT NULL
);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def audit(self, actor: str, action: str, payload: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO audit_log (ts, actor, action, payload) VALUES (?, ?, ?, ?)",
            (utcnow(), actor, action, json.dumps(payload, default=str)),
        )
        self._conn.commit()

    def log_decision(self, backend: str, request: dict[str, Any], response: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO decisions (ts, backend, request, response) VALUES (?, ?, ?, ?)",
            (utcnow(), backend, json.dumps(request, default=str), json.dumps(response, default=str)),
        )
        self._conn.commit()

    def upsert_factor(self, factor_id: str, name: str, family: str, spec: dict[str, Any]) -> None:
        self._conn.execute(
            """INSERT INTO factors (id, name, family, spec, created)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET name=excluded.name, spec=excluded.spec""",
            (factor_id, name, family, json.dumps(spec), utcnow()),
        )
        self._conn.commit()

    def add_hypothesis(self, hyp_id: str, factor_id: str, title: str, description: str, status: str) -> None:
        self._conn.execute(
            """INSERT INTO hypotheses (id, factor_id, title, description, status, created)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET status=excluded.status, description=excluded.description""",
            (hyp_id, factor_id, title, description, status, utcnow()),
        )
        self._conn.commit()

    def add_evaluation(
        self, factor_id: str, market_id: str, symbol: str, metrics: dict[str, Any], passed: bool
    ) -> None:
        self._conn.execute(
            """INSERT INTO evaluations (factor_id, market_id, symbol, metrics, passed, created)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (factor_id, market_id, symbol, json.dumps(metrics, default=str), int(passed), utcnow()),
        )
        self._conn.commit()

    def set_promotion(self, factor_id: str, state: str, reason: str) -> None:
        self._conn.execute(
            """INSERT INTO promotions (factor_id, state, reason, updated)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(factor_id) DO UPDATE SET state=excluded.state, reason=excluded.reason, updated=excluded.updated""",
            (factor_id, state, reason, utcnow()),
        )
        self._conn.commit()

    def remember_failure(self, title: str, reason: str, factor_id: str | None = None) -> None:
        self._conn.execute(
            "INSERT INTO memories (factor_id, title, reason, created) VALUES (?, ?, ?, ?)",
            (factor_id, title, reason, utcnow()),
        )
        self._conn.commit()

    def add_order(self, fill: dict[str, Any]) -> None:
        self._conn.execute(
            """INSERT INTO orders (id, market_id, symbol, side, quantity, price, fee, mode, factor_id, ts)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                fill["id"],
                fill["market_id"],
                fill["symbol"],
                fill["side"],
                fill["quantity"],
                fill["price"],
                fill["fee"],
                fill["mode"],
                fill.get("factor_id"),
                fill["ts"],
            ),
        )
        self._conn.commit()

    def add_risk_event(self, book: str, kind: str, detail: dict[str, Any]) -> None:
        self._conn.execute(
            "INSERT INTO risk_events (ts, book, kind, detail) VALUES (?, ?, ?, ?)",
            (utcnow(), book, kind, json.dumps(detail, default=str)),
        )
        self._conn.commit()

    def fetchall(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def fetchone(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        row = self._conn.execute(sql, params).fetchone()
        return dict(row) if row else None
