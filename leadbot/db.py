import re
import sqlite3
from pathlib import Path

DB_PATH = Path("leads.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY,
  source_id TEXT UNIQUE,
  name TEXT, niche TEXT, city TEXT,
  country TEXT, lang TEXT, tz TEXT,
  phone TEXT, email TEXT, website TEXT, instagram TEXT, context TEXT,
  score INTEGER, reason TEXT, message TEXT,
  status TEXT NOT NULL DEFAULT 'new',
  queue_channel TEXT,
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
    r"\b(pare|parar|sair|stop|remover|remova|descadastrar|n[aã]o quero|cancelar|spam|"
    r"baja|no quiero|dejar de|eliminar|no me escriban|unsubscribe|remove me|opt.?out|do not contact)\b",
    re.I,
)


def normalize_phone(raw: str | None, default_cc: str | None = "55") -> str | None:
    """Só dígitos com DDI. Com '+', respeita o DDI; sem '+', usa default_cc se o número for local."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if not raw.strip().startswith("+") and default_cc and len(digits) <= 11:
        digits = default_cc + digits.lstrip("0")
    return digits if 10 <= len(digits) <= 15 else None


def contact_key(contact: str) -> str:
    """Chave de comparação: e-mail em minúsculas ou os últimos 10 dígitos do telefone
    (evita diferenças como 52 1... do México e 54 9... da Argentina no WhatsApp)."""
    if "@" in contact:
        return contact.strip().lower()
    return re.sub(r"\D", "", contact)[-10:]


def is_optout_text(text: str) -> bool:
    return bool(OPTOUT_WORDS.search(text or ""))


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def add_lead(con, **f) -> bool:
    """Insere lead novo. Ignora duplicados e quem já pediu para sair."""
    f["phone"] = normalize_phone(f.get("phone"), f.pop("cc", None))
    keys = [contact_key(c) for c in (f["phone"], f.get("email")) if c]
    for k in keys:
        if con.execute("SELECT 1 FROM optout WHERE contact=?", (k,)).fetchone():
            return False
    if f["phone"] and con.execute(
            "SELECT 1 FROM leads WHERE substr(phone,-10)=?", (contact_key(f["phone"]),)).fetchone():
        return False
    cols = ", ".join(f)
    marks = ", ".join("?" for _ in f)
    cur = con.execute(f"INSERT OR IGNORE INTO leads ({cols}) VALUES ({marks})", list(f.values()))
    con.commit()
    return cur.rowcount == 1


def find_by_phone(con, phone: str):
    return con.execute("SELECT * FROM leads WHERE substr(phone,-10)=?", (contact_key(phone),)).fetchone()


def opt_out(con, contact: str):
    k = contact_key(contact)
    con.execute("INSERT OR IGNORE INTO optout VALUES (?)", (k,))
    con.execute("UPDATE leads SET status='opted_out' WHERE substr(phone,-10)=? OR lower(email)=?", (k, k))
    con.commit()


def log_message(con, lead_id, direction, channel, body):
    con.execute(
        "INSERT INTO messages (lead_id, direction, channel, body) VALUES (?,?,?,?)",
        (lead_id, direction, channel, body),
    )
    con.commit()
