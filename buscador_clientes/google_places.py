"""Busca no Google Maps pela API oficial (Places API - New).

Precisa de uma chave de API do Google Cloud. O Google dá um crédito mensal
gratuito que cobre milhares de buscas; veja o README para criar a chave.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from .http import post_json
from .modelo import Lead

URL = "https://places.googleapis.com/v1/places:searchText"
CAMPOS = ",".join(
    [
        "places.displayName",
        "places.formattedAddress",
        "places.nationalPhoneNumber",
        "places.internationalPhoneNumber",
        "places.websiteUri",
        "places.rating",
        "places.userRatingCount",
        "places.googleMapsUri",
        "places.businessStatus",
        "nextPageToken",
    ]
)


# O Google dá 1.000 consultas grátis por mês para buscas que trazem telefone, site e
# avaliações. Paramos antes disso, com folga, para a conta nunca ser cobrada.
LIMITE_MENSAL_PADRAO = 900


class LimiteMensalAtingido(Exception):
    pass


class ContadorUso:
    """Conta as consultas ao Google no mês e bloqueia quando chega no limite."""

    def __init__(self, arquivo, limite):
        self.arquivo = Path(arquivo)
        self.limite = limite
        try:
            self.dados = json.loads(self.arquivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.dados = {}

    @property
    def mes(self):
        return f"{datetime.now():%Y-%m}"

    @property
    def usados(self):
        return self.dados.get(self.mes, 0)

    def registrar(self):
        if self.usados >= self.limite:
            raise LimiteMensalAtingido(
                f"Limite de {self.limite} consultas ao Google neste mês atingido. "
                "Para não gastar nada, as buscas no Google voltam no mês que vem "
                "(o OpenStreetMap continua grátis: use --fonte osm)."
            )
        self.dados[self.mes] = self.usados + 1
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        self.arquivo.write_text(json.dumps(self.dados), encoding="utf-8")


def buscar(chave_api, termo, cidade, nicho, max_resultados=60, log=print, contador=None):
    """Devolve até `max_resultados` (o Google limita a 60) leads para "termo em cidade"."""
    leads = []
    corpo = {"textQuery": f"{termo} em {cidade}", "languageCode": "pt-BR", "regionCode": "BR", "pageSize": 20}
    cabecalhos = {"X-Goog-Api-Key": chave_api, "X-Goog-FieldMask": CAMPOS}
    while len(leads) < max_resultados:
        if contador:
            contador.registrar()
        resposta = post_json(URL, corpo, cabecalhos)
        for lugar in resposta.get("places", []):
            if lugar.get("businessStatus") not in (None, "OPERATIONAL"):
                continue  # fechado temporária ou definitivamente
            leads.append(
                Lead(
                    nome=lugar.get("displayName", {}).get("text", ""),
                    nicho=nicho,
                    fonte="Google Maps",
                    endereco=lugar.get("formattedAddress", ""),
                    cidade=cidade,
                    telefone=lugar.get("nationalPhoneNumber") or lugar.get("internationalPhoneNumber", ""),
                    site=lugar.get("websiteUri", ""),
                    nota=lugar.get("rating"),
                    avaliacoes=lugar.get("userRatingCount"),
                    link_mapa=lugar.get("googleMapsUri", ""),
                )
            )
        token = resposta.get("nextPageToken")
        if not token:
            break
        corpo["pageToken"] = token
        time.sleep(1)  # o token da próxima página demora um instante para valer
    log(f"  Google Maps: {len(leads)} encontrados para '{termo}'")
    return leads[:max_resultados]
