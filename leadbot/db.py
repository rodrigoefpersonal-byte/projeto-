import re
import sqlite3
from pathlib import Path

DB_PATH = Path("leads.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY,
  source_id TEXT UNIQUE,
  name TEXT, niche TEXT, city TEXT,
  phone TEXT, email TEXT, website TEXT, instagram TEXT, context TEXT,
  score INTEGER, reason TEXT, message TEXT,
  status TEXT NOT NULL DEFAULT 'new',
  contacted_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY,
  lead_id INTEGER, direction TEXT, channel TEXT, body TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS optout (contact TEXT PRIMARY KEY);
"""

OPTOUT_WORDS = re.compile(
    r"\b(pare|parar|sair|stop|remover|remova|descadastrar|n[aã]o quero|cancelar|spam)\b", re.I
)


def normalize_phone(raw: str | None) -> str | None:
    """Devolve só dígitos com DDI (assume Brasil se vier sem)."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("0"):
        digits = digits.lstrip("0")
    if len(digits) in (10, 11):
        digits = "55" + digits
    return digits if 12 <= len(digits) <= 13 else None


def is_optout_text(text: str) -> bool:
    return bool(OPTOUT_WORDS.search(text or ""))


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def add_lead(con, **f) -> bool:
    """Insere lead novo. Ignora duplicados e quem já pediu para sair."""
    f["phone"] = normalize_phone(f.get("phone"))
    for c in (f["phone"], (f.get("email") or "").lower() or None):
        if c and con.execute("SELECT 1 FROM optout WHERE contact=?", (c,)).fetchone():
            return False
    if f["phone"] and con.execute("SELECT 1 FROM leads WHERE phone=?", (f["phone"],)).fetchone():
        return False
    cols = ", ".join(f)
    marks = ", ".join("?" for _ in f)
    cur = con.execute(f"INSERT OR IGNORE INTO leads ({cols}) VALUES ({marks})", list(f.values()))
    con.commit()
    return cur.rowcount == 1


def opt_out(con, contact: str):
    contact = normalize_phone(contact) or contact.lower()
    con.execute("INSERT OR IGNORE INTO optout VALUES (?)", (contact,))
    con.execute("UPDATE leads SET status='opted_out' WHERE phone=? OR lower(email)=?", (contact, contact))
    con.commit()


def log_message(con, lead_id, direction, channel, body):
    con.execute(
        "INSERT INTO messages (lead_id, direction, channel, body) VALUES (?,?,?,?)",
        (lead_id, direction, channel, body),
    )
    con.commit()
