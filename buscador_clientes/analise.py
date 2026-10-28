"""Visita o site de cada negócio, descobre redes sociais/contatos e dá uma nota ao lead."""

import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from .http import ErroHTTP, get_texto
from .nichos import NICHOS

REDES = {
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/(?!p/|reel/|explore/|accounts/)([A-Za-z0-9_.]+)", re.I),
    "facebook": re.compile(r"https?://(?:www\.|m\.)?facebook\.com/(?!sharer|share|plugins|dialog|tr\b)([A-Za-z0-9_.\-]+)", re.I),
    "youtube": re.compile(r"https?://(?:www\.)?youtube\.com/(?:@|channel/|c/|user/)[A-Za-z0-9_.\-]+", re.I),
    "tiktok": re.compile(r"https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.]+", re.I),
    "whatsapp": re.compile(r"https?://(?:api\.whatsapp\.com/send\?phone=|wa\.me/)(\d{10,13})", re.I),
}
EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
EMAIL_FALSO = re.compile(r"\.(png|jpe?g|gif|webp|svg)$|example\.|sentry|wixpress|@\d|seudominio|email\.com$", re.I)


def extrair_contatos(html):
    """Procura links de redes sociais, WhatsApp e e-mail dentro do HTML."""
    achados = {}
    for rede, padrao in REDES.items():
        m = padrao.search(html)
        if m:
            achados[rede] = m.group(1) if rede == "whatsapp" else m.group(0)
    for email in EMAIL.findall(html):
        if not EMAIL_FALSO.search(email):
            achados["email"] = email.lower()
            break
    return achados


def analisar_site(lead):
    if not lead.site:
        return
    url = lead.site if lead.site.startswith("http") else f"http://{lead.site}"
    host = urllib.parse.urlparse(url).netloc.lower()
    # Às vezes o "site" cadastrado já é a página do Instagram/Facebook.
    for rede in ("instagram", "facebook"):
        if rede in host:
            if not getattr(lead, rede):
                setattr(lead, rede, url)
            return
    try:
        html = get_texto(url)
    except ErroHTTP:
        return
    for campo, valor in extrair_contatos(html).items():
        if not getattr(lead, campo):
            setattr(lead, campo, valor)


def analisar_sites(leads, threads=10, log=print):
    com_site = [l for l in leads if l.site]
    if not com_site:
        return
    log(f"Analisando {len(com_site)} sites para achar Instagram, WhatsApp e e-mail...")
    with ThreadPoolExecutor(max_workers=threads) as pool:
        list(pool.map(analisar_site, com_site))


def pontuar(lead):
    """Nota de 0 a 100: quanto maior, mais chance de o negócio comprar edição de vídeo."""
    pontos, motivos = 0, []

    peso = NICHOS.get(lead.nicho, {}).get("peso", 10)
    pontos += peso
    if peso >= 12:
        motivos.append("nicho que usa muito vídeo")

    if lead.instagram or lead.tiktok or lead.facebook:
        pontos += 20
        motivos.append("ativo nas redes sociais")
    if lead.youtube or lead.tiktok:
        pontos += 10
        motivos.append("já publica vídeos (pode terceirizar a edição)")
    elif lead.instagram:
        pontos += 10
        motivos.append("tem Instagram mas não tem YouTube/TikTok (oportunidade)")

    if lead.whatsapp or eh_celular(lead.telefone):
        pontos += 15
        motivos.append("tem WhatsApp/celular")
    elif lead.telefone:
        pontos += 8
    if lead.email:
        pontos += 5
    if lead.site:
        pontos += 5

    if lead.avaliacoes:
        if lead.avaliacoes >= 200:
            pontos += 15
            motivos.append(f"{lead.avaliacoes} avaliações (negócio grande)")
        elif lead.avaliacoes >= 50:
            pontos += 10
            motivos.append(f"{lead.avaliacoes} avaliações")
        elif lead.avaliacoes >= 10:
            pontos += 5
    if lead.nota and lead.nota >= 4.5:
        pontos += 5

    if not (lead.telefone or lead.whatsapp or lead.email or lead.instagram):
        pontos = min(pontos, 20)
        motivos.append("sem contato encontrado")

    lead.pontuacao = min(pontos, 100)
    lead.motivos = motivos


def so_digitos(texto):
    return "".join(c for c in texto or "" if c.isdigit())


def normalizar_telefone_br(telefone):
    """Devolve o telefone no formato 55DDDNUMERO, ou '' se não parecer válido."""
    d = so_digitos(telefone)
    if d.startswith("0"):
        d = d.lstrip("0")
        if len(d) in (12, 13):  # 0 + operadora (ex.: 021) + DDD + número
            d = d[2:]
    if d.startswith("55") and len(d) in (12, 13):
        return d
    if len(d) in (10, 11):
        return "55" + d
    return ""


def eh_celular(telefone):
    d = normalizar_telefone_br(telefone)
    return len(d) == 13 and d[4] == "9"


def link_whatsapp(lead, mensagem):
    numero = normalizar_telefone_br(lead.whatsapp) or (
        normalizar_telefone_br(lead.telefone) if eh_celular(lead.telefone) else ""
    )
    if not numero:
        return ""
    texto = mensagem.replace("{nome}", lead.nome).replace("{nicho}", NICHOS.get(lead.nicho, {}).get("busca", lead.nicho))
    return f"https://wa.me/{numero}?text={urllib.parse.quote(texto)}"
