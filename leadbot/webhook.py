"""Recebe respostas do WhatsApp, respeita pedidos de saída e responde com IA."""
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from . import ai, channels, db
from .text import t

app = FastAPI()
CFG: dict = {}


@app.get("/webhook")
def verify(request: Request):
    q = request.query_params
    if q.get("hub.verify_token") == os.environ.get("WA_VERIFY_TOKEN"):
        return PlainTextResponse(q.get("hub.challenge", ""))
    raise HTTPException(403)


@app.post("/webhook")
async def receive(request: Request):
    data = await request.json()
    con = db.connect()
    for entry in data.get("entry", []):
        for ch in entry.get("changes", []):
            for m in ch.get("value", {}).get("messages", []):
                if m.get("type") != "text":
                    continue
                handle(con, m["from"], m["text"]["body"])
    return {"ok": True}


def handle(con, phone: str, text: str):
    lead = db.find_by_phone(con, phone)
    if not lead:
        return
    db.log_message(con, lead["id"], "in", "whatsapp", text)
    if db.is_optout_text(text):
        db.opt_out(con, phone)
        channels.wa_send_text(phone, t(lead["lang"], "bye"))
        return
    history = [dict(r) for r in con.execute(
        "SELECT direction, body FROM messages WHERE lead_id=? ORDER BY id", (lead["id"],))]
    res = ai.handle_reply(CFG, {"name": lead["name"], "niche": lead["niche"]}, history, text)
    con.execute("UPDATE leads SET status=? WHERE id=?",
                ("not_interested" if res.get("intent") == "not_interested" else "replied", lead["id"]))
    con.commit()
    n_in = con.execute("SELECT COUNT(*) FROM messages WHERE lead_id=? AND direction='in'", (lead["id"],)).fetchone()[0]
    # a IA só atende a 1ª resposta do cliente; depois disso a conversa é sua
    if CFG["send"]["auto_reply"] and n_in == 1 and res.get("reply"):
        channels.wa_send_text(phone, res["reply"])
        db.log_message(con, lead["id"], "out", "whatsapp", res["reply"])
    if n_in > 1 or res.get("needs_human") or res.get("intent") == "interested":
        channels.wa_send_text(os.environ["OWNER_WHATSAPP"],
                              f"🔥 Cliente respondeu: {lead['name']} ({phone})\nDisse: {text}")


@app.get("/unsub", response_class=HTMLResponse)
def unsub(e: str):
    db.opt_out(db.connect(), e)
    lead = db.connect().execute("SELECT lang FROM leads WHERE lower(email)=?", (e.lower(),)).fetchone()
    return f"<h3>{t(lead['lang'] if lead else None, 'unsub_ok')}</h3>"
