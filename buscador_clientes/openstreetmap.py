"""Busca gratuita no OpenStreetMap (não precisa de chave nem cadastro).

Tem menos telefones e sites que o Google Maps, mas é 100% grátis.
"""

import time

from .http import get_json, post_form
from .modelo import Lead
from .nichos import NICHOS

NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = "https://overpass-api.de/api/interpreter"


def localizar_cidade(cidade):
    """Devolve o id de área do Overpass para a cidade (ou None)."""
    resultados = get_json(
        NOMINATIM,
        {"q": cidade, "format": "json", "limit": 5, "countrycodes": "br", "accept-language": "pt-BR"},
    )
    for r in resultados:
        if r.get("osm_type") == "relation":
            return 3_600_000_000 + int(r["osm_id"])
    return None


def montar_consulta(area_id, nichos):
    filtros = sorted({(k, v) for n in nichos for (k, v) in NICHOS[n]["osm"]})
    linhas = [f'  nwr["{k}"="{v}"]["name"](area.cidade);' for k, v in filtros]
    return f"[out:json][timeout:120];\narea({area_id})->.cidade;\n(\n" + "\n".join(linhas) + "\n);\nout center tags;"


def _nicho_do_elemento(tags, nichos):
    for n in nichos:
        for k, v in NICHOS[n]["osm"]:
            if tags.get(k) == v:
                if n == "barbearia" and "salao" in nichos and tags.get("hairdresser") != "barber":
                    continue
                return n
    return nichos[0]


def _endereco(tags):
    partes = [tags.get("addr:street", ""), tags.get("addr:housenumber", ""), tags.get("addr:suburb", "")]
    return ", ".join(p for p in partes if p)


def buscar(cidade, nichos, log=print):
    nichos_osm = [n for n in nichos if NICHOS[n]["osm"]]
    sem_osm = [n for n in nichos if not NICHOS[n]["osm"]]
    if sem_osm:
        log(f"  OpenStreetMap não tem categoria para: {', '.join(sem_osm)} (use o Google Maps para esses)")
    if not nichos_osm:
        return []

    area_id = localizar_cidade(cidade)
    if area_id is None:
        log(f"  Não encontrei a cidade '{cidade}' no OpenStreetMap. Tente 'Cidade, UF'.")
        return []
    time.sleep(1)  # política de uso do Nominatim: no máximo 1 requisição por segundo

    dados = post_form(OVERPASS, {"data": montar_consulta(area_id, nichos_osm)})
    leads = []
    for el in dados.get("elements", []):
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        leads.append(
            Lead(
                nome=tags.get("name", ""),
                nicho=_nicho_do_elemento(tags, nichos_osm),
                fonte="OpenStreetMap",
                endereco=_endereco(tags),
                cidade=cidade,
                telefone=tags.get("phone") or tags.get("contact:phone") or tags.get("mobile", ""),
                site=tags.get("website") or tags.get("contact:website", ""),
                email=tags.get("email") or tags.get("contact:email", ""),
                instagram=tags.get("contact:instagram", ""),
                facebook=tags.get("contact:facebook", ""),
                whatsapp=tags.get("contact:whatsapp", ""),
                link_mapa=f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else "",
            )
        )
    log(f"  OpenStreetMap: {len(leads)} encontrados")
    return leads
