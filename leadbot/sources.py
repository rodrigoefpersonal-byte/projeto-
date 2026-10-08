"""Busca de leads via Google Places API (oficial)."""
import os

import httpx

URL = "https://places.googleapis.com/v1/places:searchText"
FIELDS = ",".join(
    "places." + f
    for f in (
        "id displayName nationalPhoneNumber internationalPhoneNumber websiteUri "
        "formattedAddress rating userRatingCount businessStatus"
    ).split()
) + ",nextPageToken"


def search_places(niche: str, city: str, max_results: int = 40, min_ratings: int = 0, lang: str = "pt"):
    headers = {
        "X-Goog-Api-Key": os.environ["GOOGLE_PLACES_API_KEY"],
        "X-Goog-FieldMask": FIELDS,
    }
    body = {"textQuery": f"{niche} {city}", "languageCode": lang, "pageSize": 20}
    found = 0
    while found < max_results:
        r = httpx.post(URL, json=body, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        for p in data.get("places", []):
            if p.get("businessStatus", "OPERATIONAL") != "OPERATIONAL":
                continue
            if p.get("userRatingCount", 0) < min_ratings:
                continue
            found += 1
            yield {
                "source_id": "gp:" + p["id"],
                "name": p.get("displayName", {}).get("text"),
                "niche": niche,
                "city": city,
                "phone": p.get("internationalPhoneNumber") or p.get("nationalPhoneNumber"),
                "website": p.get("websiteUri"),
                "context": f"{p.get('formattedAddress','')} | nota {p.get('rating')} ({p.get('userRatingCount')} avaliações)",
            }
        token = data.get("nextPageToken")
        if not token:
            break
        body["pageToken"] = token


OSM_URL = "https://overpass-api.de/api/interpreter"
OSM_TAGS = {  # palavra do nicho -> filtro do OpenStreetMap
    "dentista": '["amenity"="dentist"]', "estética": '["shop"="beauty"]', "academia": '["leisure"="fitness_centre"]',
    "restaurante": '["amenity"="restaurant"]', "imobili": '["office"="estate_agent"]',
    "roupas": '["shop"="clothes"]', "barbearia": '["shop"="hairdresser"]',
}


def search_osm(niche: str, city: str, max_results: int = 40):
    """Fonte gratuita (OpenStreetMap). Cobertura menor que a do Google: nem todo negócio tem telefone cadastrado."""
    flt = next((v for k, v in OSM_TAGS.items() if k in niche.lower()), None)
    if not flt:
        return
    name = city.split(",")[0].strip()
    q = (f'[out:json][timeout:60];area["name"="{name}"]["boundary"="administrative"]->.a;'
         f'nwr(area.a){flt}["name"];out center tags 400;')
    r = httpx.post(OSM_URL, data={"data": q}, timeout=90)
    r.raise_for_status()
    n = 0
    for el in r.json().get("elements", []):
        t = el.get("tags", {})
        phone = t.get("phone") or t.get("contact:phone") or t.get("contact:whatsapp")
        insta = (t.get("contact:instagram") or t.get("instagram") or "").rstrip("/").split("/")[-1].lstrip("@")
        site = t.get("website") or t.get("contact:website")
        if not (phone or insta or site):
            continue
        n += 1
        yield {"source_id": f"osm:{el['type']}{el['id']}", "name": t["name"], "niche": niche, "city": city,
               "phone": phone, "website": site, "instagram": insta or None,
               "context": t.get("addr:street", "")}
        if n >= max_results:
            break
