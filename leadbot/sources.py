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


def search_places(niche: str, city: str, max_results: int = 40, min_ratings: int = 0):
    headers = {
        "X-Goog-Api-Key": os.environ["GOOGLE_PLACES_API_KEY"],
        "X-Goog-FieldMask": FIELDS,
    }
    body = {"textQuery": f"{niche} em {city}", "languageCode": "pt-BR", "pageSize": 20}
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
