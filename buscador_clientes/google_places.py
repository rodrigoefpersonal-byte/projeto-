"""Busca no Google Maps pela API oficial (Places API - New).

Precisa de uma chave de API do Google Cloud. O Google dá um crédito mensal
gratuito que cobre milhares de buscas; veja o README para criar a chave.
"""

import time

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


def buscar(chave_api, termo, cidade, nicho, max_resultados=60, log=print):
    """Devolve até `max_resultados` (o Google limita a 60) leads para "termo em cidade"."""
    leads = []
    corpo = {"textQuery": f"{termo} em {cidade}", "languageCode": "pt-BR", "regionCode": "BR", "pageSize": 20}
    cabecalhos = {"X-Goog-Api-Key": chave_api, "X-Goog-FieldMask": CAMPOS}
    while len(leads) < max_resultados:
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
