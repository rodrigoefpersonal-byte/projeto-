"""Pega contatos públicos e contexto do site do negócio."""
import re

import httpx

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
INSTA = re.compile(r"instagram\.com/([\w.]+)")
BAD_EMAIL_SUFFIX = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")


def enrich(website: str | None) -> dict:
    if not website:
        return {}
    try:
        html = httpx.get(website, timeout=15, follow_redirects=True,
                         headers={"User-Agent": "Mozilla/5.0"}).text
    except httpx.HTTPError:
        return {}
    emails = [e for e in EMAIL.findall(html) if not e.lower().endswith(BAD_EMAIL_SUFFIX)]
    insta = INSTA.search(html)
    text = re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", html, flags=re.S)
    text = re.sub(r"\s+", " ", text)[:1500]
    return {
        "email": emails[0].lower() if emails else None,
        "instagram": insta.group(1) if insta else None,
        "context_site": text,
    }
