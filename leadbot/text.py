"""Textos fixos por idioma (pt, es, en)."""
T = {
    "pt": {"subject": "Edição de vídeo para {name}", "hello": "Olá!", "unsub": "Não quer mais receber? Clique: {url}",
           "bye": "Tudo certo, não vamos mais te enviar mensagens. Obrigado!", "unsub_ok": "Pronto, você não receberá mais nossos e-mails."},
    "es": {"subject": "Edición de video para {name}", "hello": "¡Hola!", "unsub": "¿No quieres recibir más? Haz clic: {url}",
           "bye": "Listo, no te enviaremos más mensajes. ¡Gracias!", "unsub_ok": "Listo, no recibirás más correos nuestros."},
    "en": {"subject": "Video editing for {name}", "hello": "Hi!", "unsub": "Don't want more emails? Click: {url}",
           "bye": "Done, we won't message you again. Thanks!", "unsub_ok": "Done, you won't receive more emails from us."},
}


def t(lang: str | None, key: str, **kw) -> str:
    return T.get(lang or "pt", T["pt"])[key].format(**kw)
