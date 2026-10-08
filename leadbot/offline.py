"""Modo grátis: qualifica por regras e escreve a mensagem a partir de modelos (sem IA, sem custo)."""
import random

HOOKS = {
    "dentista": "clínicas odontológicas atraem muitos pacientes com vídeos curtos de dicas e bastidores",
    "estética": "clínicas de estética vendem muito com vídeos de antes e depois e dicas rápidas",
    "academia": "academias lotam com vídeos curtos de treinos, resultados de alunos e do espaço",
    "restaurante": "vídeos curtos dos pratos e do ambiente enchem o salão",
    "imobili": "vídeos de tour pelos imóveis geram muito mais contatos do que só fotos",
    "coach": "vídeos curtos de conteúdo constroem autoridade e trazem clientes",
    "roupas": "vídeos curtos mostrando as peças vendem muito mais que só fotos",
    "barbearia": "vídeos de cortes e do ambiente atraem clientes novos todo dia",
}
GENERIC = "vídeos curtos bem editados trazem muito mais clientes pelas redes sociais"

VARIANTS = [
    "Vi o perfil da {name} e acho que {hook}.",
    "Conheci a {name} e pensei: {hook}.",
    "Olhando a {name}, percebi uma oportunidade: {hook}.",
]


def qualify(cfg: dict, lead: dict) -> dict:
    score = 60
    score += 15 if lead.get("instagram") else 0
    score += 10 if lead.get("website") else 0
    score += 10 if lead.get("phone") else 0
    niche = (lead.get("niche") or "").lower()
    hook = next((h for k, h in HOOKS.items() if k in niche), GENERIC)
    variants = cfg.get("messages") or VARIANTS
    msg = random.choice(variants).format(name=lead["name"], hook=hook)
    return {"score": min(score, 100), "reason": "regras (modo grátis)", "message": msg}
