"""Envio por canais oficiais: WhatsApp Cloud API (Meta) e e-mail SMTP."""
import os
import smtplib
from email.message import EmailMessage

import httpx

GRAPH = "https://graph.facebook.com/v21.0"


def _wa_post(payload: dict):
    r = httpx.post(
        f"{GRAPH}/{os.environ['WA_PHONE_NUMBER_ID']}/messages",
        headers={"Authorization": f"Bearer {os.environ['WA_TOKEN']}"},
        json={"messaging_product": "whatsapp", **payload}, timeout=30,
    )
    r.raise_for_status()
    return r.json()


def wa_send_template(phone: str, name: str, opener: str, template: str, code: str):
    """Primeiro contato: o WhatsApp só permite template aprovado. Variáveis: {{1}}=nome, {{2}}=frase."""
    return _wa_post({
        "to": phone, "type": "template",
        "template": {
            "name": template, "language": {"code": code},
            "components": [{"type": "body", "parameters": [
                {"type": "text", "text": name[:60]}, {"type": "text", "text": opener[:250]}]}],
        },
    })


def wa_send_text(phone: str, text: str):
    """Resposta livre (só funciona até 24h depois que o cliente escreveu)."""
    return _wa_post({"to": phone, "type": "text", "text": {"body": text}})


def send_email(to: str, subject: str, body: str, unsub_text: str = "Unsubscribe: {url}"):
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = os.environ["EMAIL_FROM"], to, subject
    unsub = f"{os.environ['PUBLIC_URL']}/unsub?e={to}"
    msg["List-Unsubscribe"] = f"<{unsub}>"
    msg.set_content(f"{body}\n\n--\n" + unsub_text.format(url=unsub))
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 587))) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)
