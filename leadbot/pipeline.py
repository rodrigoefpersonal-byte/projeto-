import csv
import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from . import ai, channels, db, enrich, sources
from .text import t


def find(cfg, con):
    s, new = cfg["search"], 0
    for tg in s["targets"]:
        for niche in s["niches"][tg["lang"]]:
            for city in tg["cities"]:
                try:
                    for p in sources.search_places(niche, city, s["max_results_per_query"],
                                                   s["min_rating_count"], tg["lang"]):
                        if db.add_lead(con, country=tg["country"], lang=tg["lang"], tz=tg["tz"],
                                       cc=tg["cc"], **p):
                            new += 1
                except Exception as e:  # noqa: BLE001 - uma cidade com erro não para o resto
                    print(f"erro buscando {niche}/{city}: {e}")
    print(f"{new} leads novos")


def qualify(cfg, con):
    rows = con.execute("SELECT * FROM leads WHERE status='new'").fetchall()
    for r in rows:
        lead = dict(r)
        extra = enrich.enrich(lead["website"])
        lead["email"] = lead["email"] or extra.get("email")
        lead["instagram"] = extra.get("instagram")
        lead["context"] = (lead["context"] or "") + " | site: " + extra.get("context_site", "")[:800]
        if not (lead["phone"] or lead["email"] or lead["instagram"]):
            con.execute("UPDATE leads SET status='rejected', reason='sem contato' WHERE id=?", (r["id"],))
            continue
        try:
            res = ai.qualify(cfg, {k: lead[k] for k in ("name", "niche", "city", "country", "context", "instagram")},
                             lead["lang"])
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


def _local_hour_ok(tz: str | None, hours) -> bool:
    now = datetime.now(ZoneInfo(tz)) if tz else datetime.now()
    return hours[0] <= now.hour < hours[1] and now.weekday() < 6


def send(cfg, con):
    s = cfg["send"]
    sent_today = con.execute(
        "SELECT COUNT(*) FROM leads WHERE date(contacted_at)=date('now')").fetchone()[0]
    room = s["daily_limit"] - sent_today
    queue = con.execute("SELECT * FROM leads WHERE status='qualified' ORDER BY score DESC").fetchall()
    for r in queue:
        if room <= 0:
            break
        direct = [c for c in s["channel_order"] if (c == "whatsapp" and r["phone"]) or (c == "email" and r["email"])]
        if direct and not _local_hour_ok(r["tz"], s["hours"]):
            continue  # fora do horário comercial NO PAÍS do lead; fica para outra rodada
        channel = None
        try:
            for ch in s["channel_order"]:
                if ch == "whatsapp" and r["phone"]:
                    tpl = s["whatsapp_templates"][r["lang"]]
                    channels.wa_send_template(r["phone"], r["name"], r["message"], tpl["name"], tpl["code"])
                    channel = ch; break
                if ch == "email" and r["email"]:
                    channels.send_email(
                        r["email"], t(r["lang"], "subject", name=r["name"]),
                        f"{t(r['lang'], 'hello')}\n\n{r['message']}\n\n{cfg['offer']}\n{cfg['portfolio_url']}\n\n{cfg['seller_name']}",
                        t(r["lang"], "unsub"))
                    channel = ch; break
                if ch == "instagram" and r["instagram"]:
                    con.execute("UPDATE leads SET status='dm_queue' WHERE id=?", (r["id"],)); con.commit()
                    break  # fila manual; não conta no limite diário
        except Exception as e:  # noqa: BLE001
            print(f"falha enviando p/ {r['name']}: {e}")
            con.execute("UPDATE leads SET status='failed' WHERE id=?", (r["id"],)); con.commit()
            continue
        if channel:
            con.execute("UPDATE leads SET status='contacted', contacted_at=datetime('now') WHERE id=?", (r["id"],))
            db.log_message(con, r["id"], "out", channel, r["message"])
            room -= 1
            print(f"enviado ({channel}): {r['name']} [{r['country']}]")
            time.sleep(random.uniform(*s["delay_seconds"]))


def dm_queue(cfg, con, path="dm_queue.csv"):
    """Instagram: a Meta não permite DM automático a quem não te escreveu. Gera a fila pronta para você enviar."""
    rows = con.execute("SELECT id,name,country,instagram,message FROM leads WHERE status='dm_queue' ORDER BY score DESC").fetchall()
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "negocio", "pais", "link_dm", "mensagem"])
        for r in rows:
            w.writerow([r["id"], r["name"], r["country"], f"https://ig.me/m/{r['instagram']}", r["message"]])
    print(f"{len(rows)} DMs prontas em {path}")


def dm_done(con, ids):
    for i in ids:
        con.execute("UPDATE leads SET status='contacted', contacted_at=datetime('now') WHERE id=? AND status='dm_queue'", (i,))
    con.commit()


def run_all(cfg, con):
    find(cfg, con); qualify(cfg, con); send(cfg, con); dm_queue(cfg, con)
