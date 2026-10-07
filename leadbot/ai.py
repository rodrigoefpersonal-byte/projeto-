"""Claude: qualifica o lead, escreve a mensagem personalizada e responde clientes."""
import json
import os
import re

import anthropic

_client = None


def _ask(model: str, system: str, user: str, max_tokens=600) -> dict:
    global _client
    _client = _client or anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = _client.messages.create(
        model=model, max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}],
    )
    text = msg.content[0].text
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


def qualify(cfg: dict, lead: dict, lang: str = "pt") -> dict:
    """-> {score:int, reason:str, message:str}. message = 1 frase de abertura (máx 200 caracteres)."""
    system = (
        "Você ajuda um editor de vídeo freelancer a prospectar clientes no Brasil. "
        "Responda APENAS com JSON: {\"score\":0-100,\"reason\":\"...\",\"message\":\"...\"}. "
        f"IMPORTANTE: escreva 'message' no idioma '{lang}' (pt=português, es=español, en=English). "
        "score = chance do negócio precisar/pagar por edição de vídeo (vende por vídeo? tem redes sociais? "
        "é negócio local ativo?). 'message' é UMA frase curta, natural (foque em UM benefício: 'você grava, eu cuido do resto', sem listar todo o pacote), no idioma indicado, que cita algo "
        "específico do negócio e conecta com vídeo. Sem exageros, sem emojis em excesso, sem mentir."
    )
    user = f"Oferta: {cfg['offer']}\nLead: {json.dumps(lead, ensure_ascii=False)}"
    return _ask(cfg["qualify"]["model"], system, user)


def handle_reply(cfg: dict, lead: dict, history: list[dict], incoming: str) -> dict:
    # responde no idioma em que o cliente escreveu
    """-> {intent: interested|question|not_interested|other, reply:str, needs_human:bool}"""
    system = (
        f"Você é assistente de {cfg['seller_name']}, editor de vídeo. Oferta: {cfg['offer']} "
        f"Portfólio: {cfg['portfolio_url']}. Responda APENAS JSON: "
        "{\"intent\":\"interested|question|not_interested|other\",\"reply\":\"...\",\"needs_human\":bool}. "
        "Responda no mesmo idioma da mensagem do cliente. Seja breve e cordial. Nunca invente preços, prazos ou condições que não estão na oferta. "
        "Se o cliente quer fechar, pedir orçamento ou negociar, needs_human=true e reply curto avisando que "
        f"{cfg['seller_name']} vai responder em instantes. Se não tem interesse, agradeça e encerre."
    )
    user = (f"Lead: {json.dumps(lead, ensure_ascii=False)}\nHistórico: {json.dumps(history, ensure_ascii=False)}"
            f"\nMensagem nova do cliente: {incoming}")
    return _ask(cfg["qualify"]["model"], system, user)
