# Buscador de clientes para edição de vídeo

Programa que procura **automaticamente** negócios na sua cidade (academias, clínicas de estética,
imobiliárias, restaurantes, barbearias etc.) que podem comprar seus **pacotes de edição de vídeo**,
e monta uma lista pronta para você entrar em contato.

Para cada negócio ele traz:

- nome, telefone, endereço, nota e número de avaliações no Google;
- Instagram, Facebook, YouTube, TikTok, WhatsApp e e-mail (ele visita o site do negócio para achar);
- um **link pronto do WhatsApp** com a sua mensagem de apresentação já escrita;
- uma **pontuação de 0 a 100** e o motivo dela, para você começar pelos melhores clientes.

O resultado sai em 3 arquivos na pasta `resultados/`:

| Arquivo | Para quê |
|---|---|
| `clientes_....html` | Abre no navegador. Tem botão verde de WhatsApp e campo de filtro. **O mais prático.** |
| `clientes_....xlsx` | Planilha do Excel com links clicáveis e filtros. |
| `clientes_....csv`  | Mesmo conteúdo em formato simples (Excel, Google Planilhas). |

O programa guarda um histórico: **quem já apareceu numa busca não aparece de novo** na próxima,
assim você não manda mensagem duas vezes para o mesmo lugar.

---

## 1. Instalar (uma vez só)

1. Instale o **Python 3.10 ou mais novo**: <https://www.python.org/downloads/>
   (no Windows, marque a opção **"Add Python to PATH"** na instalação).
2. Baixe esta pasta (botão verde **Code → Download ZIP** no GitHub) e descompacte.
3. (Opcional, para gerar a planilha `.xlsx`) abra o terminal na pasta e rode:
   ```
   pip install -r requirements.txt
   ```
   Sem isso o programa funciona do mesmo jeito; só não gera o `.xlsx`, apenas o `.html` e o `.csv`.

## 2. Usar

**Windows:** dê dois cliques em `iniciar_windows.bat`. O programa vai perguntar a cidade e os nichos.

**Qualquer sistema (terminal):**

```
python buscar_clientes.py
```

Ou passando tudo de uma vez:

```
python buscar_clientes.py --cidade "Campinas, SP" --nichos academia,estetica,imobiliaria
```

Exemplos úteis:

```
# Várias cidades de uma vez
python buscar_clientes.py --cidade "Campinas, SP; Valinhos, SP; Sumaré, SP" --nichos academia

# Todos os nichos, só os leads mais quentes
python buscar_clientes.py --cidade "Belo Horizonte, MG" --nichos todos --min-pontuacao 60

# Um nicho que não está na lista (busca livre no Google Maps)
python buscar_clientes.py --cidade "Curitiba, PR" --nichos "nutricionista,loja de suplementos"
```

Nichos prontos: `academia, personal, estetica, salao, barbearia, imobiliaria, restaurante,
hamburgueria, cafeteria, bar, dentista, clinica, advogado, loja_roupas, concessionaria, escola,
curso, autoescola, petshop, hotel, eventos, fotografo, igreja, tatuagem, agencia, construtora, padaria`
(ou `todos`). Sem escolher nenhum, ele usa: academia, estética, imobiliária, restaurante,
barbearia, loja de roupas e dentista.

Veja todas as opções com `python buscar_clientes.py --help`.

## 3. De onde vêm os clientes

O programa tem duas fontes:

| Fonte | Custo | Qualidade |
|---|---|---|
| **OpenStreetMap** | Grátis, sem cadastro | Funciona na hora, mas muitos negócios não têm telefone/site cadastrado. |
| **Google Maps** (API oficial) | Precisa de uma chave; o Google tem uma cota gratuita mensal | Muito mais completo: telefone, site, nota e avaliações de quase todos. **Recomendado.** |

Sem chave, ele usa o OpenStreetMap automaticamente. Com chave, usa o Google Maps.
Para usar as duas juntas: `--fonte ambas`.

> O programa usa a **API oficial** do Google em vez de "raspar" a página do Google Maps.
> Raspar o site é contra os termos de uso do Google e costuma resultar em bloqueio; a API é o
> caminho permitido e estável.

### Chave do Google (recomendado)

1. Entre em <https://console.cloud.google.com/> com sua conta Google e crie um projeto.
2. Ative o faturamento (cartão) — é exigido pelo Google mesmo para usar a cota gratuita.
3. Em **APIs e serviços → Biblioteca**, ative a **"Places API (New)"**.
4. Em **APIs e serviços → Credenciais → Criar credenciais → Chave de API**. Copie a chave.
5. Crie um arquivo chamado `chave_google.txt` nesta pasta e cole a chave dentro (só a chave).

Pronto: a partir daí o programa usa o Google Maps sozinho.

**Sobre custos:** cada nicho em cada cidade faz até 3 consultas (até 60 negócios). Os campos de
telefone e site ficam numa faixa de preço mais alta da API. Confira a cota gratuita e os preços
atuais em <https://developers.google.com/maps/billing-and-pricing/pricing> e, para não ter
surpresa, defina um **limite de uso diário** em *APIs e serviços → Places API (New) → Cotas* e um
**alerta de orçamento** em *Faturamento → Orçamentos e alertas*.

## 4. Personalizar a mensagem do WhatsApp

Edite o arquivo `mensagem.txt`. Use `{nome}` onde quiser o nome do negócio. Exemplo:

```
Olá, {nome}! Vi o perfil de vocês e tenho uma proposta de vídeos para o Instagram...
```

O link do WhatsApp só é criado quando o número é de **celular** (ou quando o site do negócio tem
um botão de WhatsApp), porque telefone fixo normalmente não tem WhatsApp.

## 5. Como a pontuação funciona

Quanto maior, maior a chance de o negócio comprar edição de vídeo:

- **Nicho** que usa muito vídeo (academia, estética, imobiliária, agência...): até +15
- **Ativo nas redes sociais** (Instagram/Facebook/TikTok): +20
- Já posta vídeos no YouTube/TikTok (pode terceirizar a edição) **ou** tem Instagram mas não tem
  YouTube/TikTok (oportunidade de começar): +10
- Tem **WhatsApp/celular**: +15 (telefone fixo: +8)
- Tem e-mail: +5 · tem site: +5
- **Muitas avaliações** no Google (negócio grande, com verba): +5 a +15 · nota 4,5 ou mais: +5
- Sem nenhuma forma de contato: no máximo 20

A coluna "Por que é um bom lead" explica a nota de cada um.

## 6. Dicas de uso responsável

- São dados públicos de empresas, mas trate a lista com cuidado (LGPD): use só para oferecer
  seu serviço e pare de contatar quem pedir.
- Não dispare dezenas de mensagens iguais de uma vez no WhatsApp: personalize e envie aos poucos,
  senão o WhatsApp pode bloquear seu número.

## Para desenvolvedores

Sem dependências obrigatórias (só a biblioteca padrão do Python). Testes:

```
pip install pytest openpyxl
python -m pytest
```
