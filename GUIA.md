# Guia: do zero até rodar (modo grátis)

Os nomes de menus podem mudar um pouco; se algo não bater, procure o equivalente.
**Nunca mande chaves por chat/e-mail.** Elas ficam só no arquivo `.env` do seu computador.

## Custos reais
| Item | Custo |
|---|---|
| Servidor | **R$ 0** — roda no seu computador |
| Google Places | Tem uso gratuito mensal; precisa cadastrar cartão, e você define um **limite de gasto** (passo 2) |
| IA (Anthropic) | Pré-pago: comece com US$ 5 (dá para milhares de mensagens) |
| WhatsApp / Instagram | **R$ 0** no modo grátis (você clica e envia) |

## 1. Chave da IA (Anthropic)
1. Entre em console.anthropic.com e crie a conta.
2. Em *Billing*, adicione US$ 5 de crédito.
3. Em *API Keys*, crie uma chave e copie. No `.env`: `ANTHROPIC_API_KEY=...`

## 2. Chave do Google (busca de empresas)
1. console.cloud.google.com → entre com sua conta Google → crie um projeto ("leadbot").
2. *Faturamento*: cadastre o cartão (exigido, mas o uso inicial é coberto pelo gratuito).
3. *APIs e serviços → Biblioteca* → procure **Places API (New)** → Ativar.
4. *APIs e serviços → Credenciais → Criar credenciais → Chave de API*. Copie. No `.env`: `GOOGLE_PLACES_API_KEY=...`
5. **Segurança:** em *Faturamento → Orçamentos e alertas*, crie um alerta (ex.: R$ 30). Em *Cotas* da Places API, limite as requisições por dia.

## 3. Instalar no seu computador
1. Instale o Python 3.11+ (python.org). Baixe esta pasta do GitHub (ou `git clone`).
2. No terminal, dentro da pasta:
```
pip install -r requirements.txt
cp config.example.yaml config.yaml
cp .env.example .env      # edite e cole as 2 chaves
python -m leadbot run     # busca, qualifica e prepara a fila
```
3. Abra o arquivo **fila.html** no navegador. Cada cartão tem um botão:
   - **WhatsApp:** abre a conversa com a mensagem pronta → é só apertar enviar.
   - **Instagram:** *Copiar mensagem* e *Abrir Instagram* → cole e envie.
4. Quando terminar, rode o comando que aparece no fim da página (`python -m leadbot dm-done 1 2 3 ...`).
   Ele marca como enviado para não repetir.
5. Use 20 por dia. Rode `python -m leadbot run` uma vez por dia.

**Primeiro teste:** no `config.yaml`, deixe só 1 nicho e 1 cidade e `max_results_per_query: 5`.

## 4. Quando o negócio render (opcional, pago): automação total
Troque `channel_order` por `["whatsapp", "email", "instagram"]` e configure a WhatsApp Cloud API (Meta).
Detalhes importantes:
- A API exige um número que **não esteja ativo** no app WhatsApp/WhatsApp Business. A Meta tem um modo
  de "coexistência" que permite usar o app Business junto com a API; confira se está disponível para o seu número no painel.
- Template de primeiro contato aprovado (texto no README) e mensagens de marketing são cobradas por envio.
- Para a IA responder sozinha, o webhook precisa de endereço público (VPS, ou túnel gratuito da Cloudflare enquanto o PC estiver ligado).
