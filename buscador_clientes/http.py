"""Pequeno cliente HTTP usando apenas a biblioteca padrão (sem instalar nada)."""

import json
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "BuscadorClientes/1.0 (prospeccao de clientes para edicao de video)"


class ErroHTTP(Exception):
    pass


def _abrir(req, timeout):
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(), resp.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")[:500]
        raise ErroHTTP(f"HTTP {e.code} em {req.full_url}: {corpo}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ErroHTTP(f"Falha ao acessar {req.full_url}: {e}") from e


def get_json(url, params=None, headers=None, timeout=30):
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    dados, charset = _abrir(req, timeout)
    return json.loads(dados.decode(charset, "replace"))


def post_json(url, corpo, headers=None, timeout=30):
    req = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    dados, charset = _abrir(req, timeout)
    return json.loads(dados.decode(charset, "replace"))


def post_form(url, campos, timeout=120):
    req = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(campos).encode("utf-8"),
        headers={"User-Agent": USER_AGENT},
        method="POST",
    )
    dados, charset = _abrir(req, timeout)
    return json.loads(dados.decode(charset, "replace"))


def get_texto(url, timeout=10, limite_bytes=600_000):
    """Baixa uma página (até `limite_bytes`) e devolve o HTML como texto."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": "text/html"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dados = resp.read(limite_bytes)
            charset = resp.headers.get_content_charset() or "utf-8"
    except Exception as e:  # sites de terceiros falham de todo jeito; não derruba a busca
        raise ErroHTTP(f"Falha ao acessar {url}: {e}") from e
    return dados.decode(charset, "replace")
