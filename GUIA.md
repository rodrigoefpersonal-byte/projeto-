# Guia: modo 100% grátis (sem chaves, sem cartão)

Nesse modo o programa:
- pega leads de uma fonte gratuita (OpenStreetMap) e/ou de uma planilha CSV sua;
- escolhe a nota e escreve a mensagem com modelos prontos (sem IA);
- gera a página `fila.html` onde você clica e envia pelo WhatsApp/Instagram.

Não precisa de Anthropic, Google, Meta nem servidor. Custo: R$ 0.

## Instalar (uma vez)
1. Python 3.13 instalado (`py --version` deve funcionar no cmd).
2. Na pasta do programa: copie `config.example.yaml`, cole, e renomeie a cópia para `config.yaml`.
3. No cmd, dentro da pasta: `py -m pip install -r requirements.txt`

## Usar todo dia
1. **Leads automáticos (OpenStreetMap):** `py -m leadbot run`
   Atenção: o OpenStreetMap tem menos telefones cadastrados que o Google. Pode vir pouca coisa.
2. **Leads manuais (funciona melhor no começo):** abra o Google Maps ou o Instagram, procure
   "dentista em Curitiba" etc., anote nome/telefone/@ numa planilha com as colunas
   `nome;telefone;instagram;nicho;cidade;site` (veja `leads_exemplo.csv`), salve como CSV e rode:
   `py -m leadbot import meus_leads.csv` e depois `py -m leadbot run`
3. Abra a **fila.html** no navegador e clique nos botões. WhatsApp: abre a conversa com o texto pronto,
   é só apertar enviar. Instagram: copie a mensagem e abra o perfil.
4. No fim, rode o comando que aparece no rodapé da página: `py -m leadbot dm-done 1 2 3`
5. Máximo 20 por dia. Se não achar clientes, aumente as cidades/nichos em `config.yaml`.

## Quando o primeiro cliente pagar (opcional)
- IA para mensagens mais personalizadas: no `config.yaml`, `qualify: mode: ai`, `py -m pip install -r requirements-extra.txt`
  e `ANTHROPIC_API_KEY` no `.env` (pré-pago, a partir de ~US$ 5).
- Busca do Google (mais completa): `search: source: google` + `GOOGLE_PLACES_API_KEY`.
- Envio automático e respostas por IA no WhatsApp: API oficial da Meta (ver README).
