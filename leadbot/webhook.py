"""Recebe respostas do WhatsApp, respeita pedidos de saída e responde com IA."""
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from . import ai, channels, db

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
                handle(con, db.normalize_phone(m["from"]), m["text"]["body"])
    return {"ok": True}


def handle(con, phone: str, text: str):
    lead = con.execute("SELECT * FROM leads WHERE phone=?", (phone,)).fetchone()
    if not lead:
        return
    db.log_message(con, lead["id"], "in", "whatsapp", text)
    if db.is_optout_text(text):
        db.opt_out(con, phone)
        channels.wa_send_text(phone, "Tudo certo, não vamos mais te enviar mensagens. Obrigado!")
        return
    history = [dict(r) for r in con.execute(
        "SELECT direction, body FROM messages WHERE lead_id=? ORDER BY id", (lead["id"],))]
    res = ai.handle_reply(CFG, {"name": lead["name"], "niche": lead["niche"]}, history, text)
    con.execute("UPDATE leads SET status=? WHERE id=?",
                ("not_interested" if res.get("intent") == "not_interested" else "replied", lead["id"]))
    con.commit()
    if CFG["send"]["auto_reply"] and res.get("reply"):
        channels.wa_send_text(phone, res["reply"])
        db.log_message(con, lead["id"], "out", "whatsapp", res["reply"])
    if res.get("needs_human") or res.get("intent") == "interested":
        channels.wa_send_text(os.environ["OWNER_WHATSAPP"],
                              f"🔥 Lead quente: {lead['name']} ({phone})\nDisse: {text}")


@app.get("/unsub", response_class=HTMLResponse)
def unsub(e: str):
    db.opt_out(db.connect(), e)
    return "<h3>Pronto, você não receberá mais nossos e-mails.</h3>"
