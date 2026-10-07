import random
import time
from datetime import datetime

from . import ai, channels, db, enrich, sources


def find(cfg, con):
    s, new = cfg["search"], 0
    for niche in s["niches"]:
        for city in s["cities"]:
            for p in sources.search_places(niche, city, s["max_results_per_query"], s["min_rating_count"]):
                if db.add_lead(con, **p):
                    new += 1
    print(f"{new} leads novos")


def qualify(cfg, con):
    rows = con.execute("SELECT * FROM leads WHERE status='new'").fetchall()
    for r in rows:
        lead = dict(r)
        extra = enrich.enrich(lead["website"])
        lead["email"] = lead["email"] or extra.get("email")
        lead["instagram"] = extra.get("instagram")
        lead["context"] += " | site: " + extra.get("context_site", "")[:800]
        if not (lead["phone"] or lead["email"]):
            con.execute("UPDATE leads SET status='rejected', reason='sem contato' WHERE id=?", (r["id"],))
            continue
        try:
            res = ai.qualify(cfg, {k: lead[k] for k in ("name", "niche", "city", "context", "instagram")})
        except Exception as e:  # noqa: BLE001 - não derruba o lote por 1 falha
            print("erro IA:", e)
            continue
        ok = res.get("score", 0) >= cfg["qualify"]["min_score"]
        con.execute(
            "UPDATE leads SET email=?, instagram=?, score=?, reason=?, message=?, status=? WHERE id=?",
            (lead["email"], lead["instagram"], res.get("score"), res.get("reason"),
             res.get("message"), "qualified" if ok else "rejected", r["id"]),
        )
        con.commit()


def send(cfg, con):
    s = cfg["send"]
    h0, h1 = s["hours"]
    if not (h0 <= datetime.now().hour < h1):
        return print("fora do horário comercial")
    sent_today = con.execute(
        "SELECT COUNT(*) FROM leads WHERE date(contacted_at)=date('now','localtime')").fetchone()[0]
    queue = con.execute(
        "SELECT * FROM leads WHERE status='qualified' ORDER BY score DESC LIMIT ?",
        (max(0, s["daily_limit"] - sent_today),)).fetchall()
    for r in queue:
        channel = None
        try:
            for ch in s["channel_order"]:
                if ch == "whatsapp" and r["phone"]:
                    channels.wa_send_template(r["phone"], r["name"], r["message"]); channel = ch; break
                if ch == "email" and r["email"]:
                    channels.send_email(r["email"], f"Edição de vídeo para {r['name']}",
                                        f"Olá!\n\n{r['message']}\n\n{cfg['offer']}\nPortfólio: {cfg['portfolio_url']}\n\n{cfg['seller_name']}",
                                        r["id"]); channel = ch; break
        except Exception as e:  # noqa: BLE001
            print(f"falha enviando p/ {r['name']}: {e}")
            con.execute("UPDATE leads SET status='failed' WHERE id=?", (r["id"],)); con.commit()
            continue
        if channel:
            con.execute("UPDATE leads SET status='contacted', contacted_at=datetime('now','localtime') WHERE id=?", (r["id"],))
            db.log_message(con, r["id"], "out", channel, r["message"])
            print(f"enviado ({channel}): {r['name']}")
            time.sleep(random.uniform(*s["delay_seconds"]))


def run_all(cfg, con):
    find(cfg, con); qualify(cfg, con); send(cfg, con)
