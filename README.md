# leadbot – prospecção automática para editor de vídeo

Todo dia o robô: **acha negócios** (Google Places) → **qualifica com IA** (Claude) →
**manda mensagem personalizada** (WhatsApp oficial / e-mail) → **responde as respostas**
e te avisa no WhatsApp quando aparece um lead quente.

## Instalar
```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml   # edite nichos, cidades, oferta
cp .env.example .env                 # coloque as chaves
python -m leadbot run                # roda o ciclo completo uma vez
python -m leadbot stats              # funil de leads
python -m leadbot serve              # sobe o webhook de respostas (porta 8000)
```
Automático todo dia: `0 9 * * * cd /caminho && python -m leadbot run` (cron), ou um nó
**Schedule → Execute Command** no n8n com esse mesmo comando.

## Chaves necessárias
| O quê | Onde |
|---|---|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `GOOGLE_PLACES_API_KEY` | Google Cloud → ative "Places API (New)" |
| `WA_*` | Meta for Developers → WhatsApp Cloud API. Aponte o webhook para `https://SEU-DOMINIO/webhook` |

## Template do WhatsApp (precisa de aprovação da Meta, 1x)
Nome: `primeiro_contato_video`, idioma pt_BR, categoria Marketing:
> Olá, {{1}}! {{2}} Sou editor de vídeo e posso te mandar um vídeo de teste grátis. Se não quiser receber mensagens, responda SAIR.

## Regras de segurança embutidas
- Limite diário (`daily_limit`) e intervalo aleatório: comece com ~20/dia e suba aos poucos.
- Só envia em horário comercial.
- Quem responde "pare/sair/não quero" é bloqueado para sempre (e nunca volta a ser captado).
- E-mail sai com link de descadastro. Dados são de fontes públicas de empresas (atenção à LGPD).
- Não use WhatsApp não oficial/disparadores piratas: o número é banido rapidamente.
