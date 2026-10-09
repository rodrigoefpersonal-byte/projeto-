import html
import random
import time
from datetime import datetime
from urllib.parse import quote
from zoneinfo import ZoneInfo

import csv
import re

from . import channels, db, enrich, offline, sources
from .text import t


def find(cfg, con):
    s, new = cfg["search"], 0
    use_osm = s.get("source", "google") == "osm"
    d_cap, m_cap = s.get("google_daily_cap", 10), s.get("google_monthly_cap", 800)
    spend = lambda: db.spend_api_call(con, d_cap, m_cap)  # noqa: E731
    for tg in s["targets"]:
        for niche in s["niches"][tg["lang"]]:
            for city in tg["cities"]:
                q = f"{use_osm}:{niche}|{city}"
                if con.execute("SELECT 1 FROM done_queries WHERE q=?", (q,)).fetchone():
                    continue  # essa combinação já foi buscada; não gasta de novo
                try:
                    gen = (sources.search_osm(niche, city, s["max_results_per_query"]) if use_osm else
                           sources.search_places(niche, city, s["max_results_per_query"], s["min_rating_count"],
                                                tg["lang"], before_call=spend))
                    for p in gen:
                        if db.add_lead(con, country=tg["country"], lang=tg["lang"], tz=tg["tz"], cc=tg["cc"], **p):
                            new += 1
                    con.execute("INSERT OR IGNORE INTO done_queries VALUES (?)", (q,)); con.commit()
                except db.BudgetExceeded as e:
                    print(f"{new} leads novos. Parei: {e}")
                    return
                except Exception as e:  # noqa: BLE001 - uma cidade com erro não para o resto
                    print(f"erro buscando {niche}/{city}: {e}")
    print(f"{new} leads novos")


def qualify(cfg, con):
    rows = con.execute("SELECT * FROM leads WHERE status='new'").fetchall()
    for r in rows:
        lead = dict(r)
        extra = enrich.enrich(lead["website"])
        lead["email"] = lead["email"] or extra.get("email")
        lead["instagram"] = lead["instagram"] or extra.get("instagram")
        lead["context"] = (lead["context"] or "") + " | site: " + extra.get("context_site", "")[:800]
        if not (lead["phone"] or lead["email"] or lead["instagram"]):
            con.execute("UPDATE leads SET status='rejected', reason='sem contato' WHERE id=?", (r["id"],))
            continue
        try:
            info = {k: lead[k] for k in ("name", "niche", "city", "country", "context", "instagram", "website", "phone")}
            if cfg["qualify"].get("mode", "ai") == "ai":
                from . import ai  # só carrega (e exige chave) se o modo IA estiver ligado
                res = ai.qualify(cfg, info, lead["lang"])
            else:
                res = offline.qualify(cfg, info)
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
    pending = con.execute("SELECT COUNT(*) FROM leads WHERE status='dm_queue'").fetchone()[0]
    room = s["daily_limit"] - sent_today - pending
    queue = con.execute("SELECT * FROM leads WHERE status='qualified' ORDER BY score DESC").fetchall()
    for r in queue:
        if room <= 0:
            break
        first = next((c for c in s["channel_order"] if (c in ("whatsapp", "whatsapp_manual") and r["phone"])
                     or (c == "email" and r["email"]) or (c == "instagram" and r["instagram"])), None)
        if first in ("whatsapp", "email") and not _local_hour_ok(r["tz"], s["hours"]):
            continue  # fora do horário comercial NO PAÍS do lead; fica para outra rodada
        channel = queue = None
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
                if ch == "whatsapp_manual" and r["phone"]:
                    queue = "whatsapp"
                    break
                if ch == "instagram" and r["instagram"]:
                    queue = "instagram"
                    break
        except Exception as e:  # noqa: BLE001
            print(f"falha enviando p/ {r['name']}: {e}")
            con.execute("UPDATE leads SET status='failed' WHERE id=?", (r["id"],)); con.commit()
            continue
        if queue:  # fila manual: você clica e envia (ver `leadbot dm`)
            con.execute("UPDATE leads SET status='dm_queue', queue_channel=? WHERE id=?", (queue, r["id"]))
            con.commit()
            room -= 1
            print(f"na fila ({queue}): {r['name']}")
        elif channel:
            con.execute("UPDATE leads SET status='contacted', contacted_at=datetime('now') WHERE id=?", (r["id"],))
            db.log_message(con, r["id"], "out", channel, r["message"])
            room -= 1
            print(f"enviado ({channel}): {r['name']} [{r['country']}]")
            time.sleep(random.uniform(*s["delay_seconds"]))


def full_text(cfg, r) -> str:
    return (f"Olá, {r['name']}! {r['message']}\n\nSou o {cfg['seller_name']}: escrevo o roteiro e edito os seus vídeos "
            f"(com thumbnail e tudo). Posso fazer um vídeo de teste grátis? Portfólio: {cfg['portfolio_url']}\n"
            "Se não quiser receber mensagens, é só avisar.")


def dm_queue(cfg, con, path="fila.html"):
    """Gera uma página com os botões prontos. Instagram não permite DM automático; WhatsApp manual é o modo grátis."""
    rows = con.execute("SELECT * FROM leads WHERE status='dm_queue' ORDER BY score DESC").fetchall()
    cards = []
    for r in rows:
        text = full_text(cfg, r)
        if r["queue_channel"] == "whatsapp":
            btn = f'<a class="b" target="_blank" href="https://wa.me/{r["phone"]}?text={quote(text)}">Abrir WhatsApp com a mensagem</a>'
        else:
            btn = (f'<button class="b" onclick="navigator.clipboard.writeText(this.dataset.t)" data-t="{html.escape(text, quote=True)}">1. Copiar mensagem</button> '
                   f'<a class="b" target="_blank" href="https://ig.me/m/{r["instagram"]}">2. Abrir Instagram</a>')
        cards.append(f'<div class="c"><b>#{r["id"]} {html.escape(r["name"])}</b> <small>({r["city"]}, nota {r["score"]})</small>'
                     f'<p>{html.escape(text)}</p>{btn}</div>')
    ids = " ".join(str(r["id"]) for r in rows)
    page = ("<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'><title>Fila</title>"
            "<style>body{font-family:sans-serif;max-width:720px;margin:20px auto;padding:0 12px}.c{border:1px solid #ccc;border-radius:8px;padding:12px;margin:10px 0}"
            ".b{display:inline-block;background:#128c7e;color:#fff;padding:8px 12px;border-radius:6px;text-decoration:none;border:0;cursor:pointer;font-size:14px}</style>"
            f"<h2>{len(rows)} mensagens para enviar hoje</h2>" + "".join(cards) +
            f"<p>Quando terminar, rode: <code>python -m leadbot dm-done {ids}</code></p>")
    open(path, "w", encoding="utf-8").write(page)
    print(f"{len(rows)} mensagens prontas em {path} (abra no navegador)")


def dm_done(con, ids):
    for i in ids:
        con.execute("UPDATE leads SET status='contacted', contacted_at=datetime('now') WHERE id=? AND status='dm_queue'", (i,))
    con.commit()


def run_all(cfg, con):
    find(cfg, con); qualify(cfg, con); send(cfg, con); dm_queue(cfg, con)


def import_csv(cfg, con, path):
    """Importa leads de uma planilha CSV (colunas: nome, telefone, instagram, nicho, cidade, site)."""
    tg = cfg["search"]["targets"][0]
    n = 0
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(2048); f.seek(0)
        for row in csv.DictReader(f, delimiter=";" if sample.count(";") > sample.count(",") else ","):
            row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
            insta = re.sub(r"[?#].*$", "", row.get("instagram", "")).rstrip("/").split("/")[-1].lstrip("@") or None
            phone = row.get("telefone") or row.get("whatsapp") or None
            if not row.get("nome") or not (phone or insta):
                continue
            key = "csv:" + (phone or insta or row["nome"])
            if db.add_lead(con, source_id=key, name=row["nome"], niche=row.get("nicho"), city=row.get("cidade"),
                           phone=phone, instagram=insta, website=row.get("site") or None, context="",
                           country=tg["country"], lang=tg["lang"], tz=tg["tz"], cc=tg["cc"]):
                n += 1
    print(f"{n} leads importados de {path}")
