"""Tipos de negócio que costumam contratar edição de vídeo.

Cada nicho tem:
  - busca:  o termo usado no Google Maps ("academia em Campinas")
  - osm:    as etiquetas equivalentes no OpenStreetMap (chave, valor)
  - peso:   o quanto esse tipo de negócio costuma investir em vídeo (0 a 15),
            usado na pontuação do lead
"""

NICHOS = {
    "academia": {"busca": "academia", "osm": [("leisure", "fitness_centre"), ("leisure", "sports_centre")], "peso": 15},
    "personal": {"busca": "personal trainer", "osm": [], "peso": 15},
    "estetica": {"busca": "clínica de estética", "osm": [("shop", "beauty")], "peso": 15},
    "salao": {"busca": "salão de beleza", "osm": [("shop", "hairdresser")], "peso": 12},
    "barbearia": {"busca": "barbearia", "osm": [("shop", "hairdresser")], "peso": 12},
    "imobiliaria": {"busca": "imobiliária", "osm": [("office", "estate_agent")], "peso": 15},
    "restaurante": {"busca": "restaurante", "osm": [("amenity", "restaurant")], "peso": 10},
    "hamburgueria": {"busca": "hamburgueria", "osm": [("amenity", "fast_food")], "peso": 10},
    "cafeteria": {"busca": "cafeteria", "osm": [("amenity", "cafe")], "peso": 8},
    "bar": {"busca": "bar", "osm": [("amenity", "bar"), ("amenity", "pub")], "peso": 8},
    "dentista": {"busca": "dentista", "osm": [("amenity", "dentist"), ("healthcare", "dentist")], "peso": 12},
    "clinica": {"busca": "clínica médica", "osm": [("amenity", "clinic")], "peso": 10},
    "advogado": {"busca": "escritório de advocacia", "osm": [("office", "lawyer")], "peso": 8},
    "loja_roupas": {"busca": "loja de roupas", "osm": [("shop", "clothes"), ("shop", "boutique")], "peso": 12},
    "concessionaria": {"busca": "concessionária de veículos", "osm": [("shop", "car")], "peso": 12},
    "escola": {"busca": "escola particular", "osm": [("amenity", "school")], "peso": 8},
    "curso": {"busca": "escola de idiomas", "osm": [("amenity", "language_school"), ("amenity", "college")], "peso": 10},
    "autoescola": {"busca": "autoescola", "osm": [("amenity", "driving_school")], "peso": 8},
    "petshop": {"busca": "pet shop", "osm": [("shop", "pet")], "peso": 8},
    "hotel": {"busca": "hotel pousada", "osm": [("tourism", "hotel"), ("tourism", "guest_house")], "peso": 12},
    "eventos": {"busca": "espaço de eventos buffet", "osm": [("amenity", "events_venue")], "peso": 12},
    "fotografo": {"busca": "fotógrafo", "osm": [("craft", "photographer"), ("shop", "photo")], "peso": 12},
    "igreja": {"busca": "igreja", "osm": [("amenity", "place_of_worship")], "peso": 8},
    "tatuagem": {"busca": "estúdio de tatuagem", "osm": [("shop", "tattoo")], "peso": 10},
    "agencia": {"busca": "agência de marketing digital", "osm": [("office", "advertising_agency")], "peso": 15},
    "construtora": {"busca": "construtora", "osm": [("office", "construction_company")], "peso": 10},
    "padaria": {"busca": "padaria confeitaria", "osm": [("shop", "bakery"), ("shop", "pastry")], "peso": 6},
}

# Usados quando a pessoa não escolhe nenhum nicho.
NICHOS_PADRAO = ["academia", "estetica", "imobiliaria", "restaurante", "barbearia", "loja_roupas", "dentista"]


def resolver_nichos(nomes):
    """Converte uma lista de nomes (ou 'todos') em chaves válidas de NICHOS.

    Um termo desconhecido vira uma busca livre: assim dá para procurar
    qualquer coisa no Google Maps, por exemplo "nutricionista".
    """
    if not nomes:
        return list(NICHOS_PADRAO)
    if any(n.strip().lower() == "todos" for n in nomes):
        return list(NICHOS)
    resultado = []
    for nome in nomes:
        chave = nome.strip().lower()
        if not chave:
            continue
        if chave not in NICHOS:
            NICHOS[chave] = {"busca": nome.strip(), "osm": [], "peso": 10}
        if chave not in resultado:
            resultado.append(chave)
    return resultado
