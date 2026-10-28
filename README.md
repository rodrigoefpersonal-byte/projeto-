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

## Jeito mais fácil: pelo navegador, sem instalar nada (Google Colab)

Funciona no computador **e no celular**, só precisa de uma conta Google.

1. Abra o caderno: <https://colab.research.google.com/github/rodrigoefpersonal-byte/projeto-/blob/main/Buscador_de_Clientes.ipynb>
   (na primeira vez o Colab pede para autorizar o GitHub, porque o repositório é privado; marque
   a opção de incluir repositórios privados). Outra opção: baixe o arquivo `Buscador_de_Clientes.ipynb`
   e, no Colab, use **Arquivo → Fazer upload de notebook**.
2. Clique em **Arquivo → Salvar uma cópia no Drive**. A partir daí abra sempre essa cópia
   (ela fica em *Meu Drive → Colab Notebooks*).
3. *(Uma vez só)* Clique na chave 🔑 na barra da esquerda → **Adicionar novo secret** →
   nome `GOOGLE_MAPS_API_KEY` e cole sua chave do Google (seção 3) → ative o acesso do notebook.
4. Clique no ▶ do **Passo 1**, preencha cidade e nichos no **Passo 2** e clique no ▶.
   A lista aparece na tela, a planilha é baixada e tudo fica salvo na pasta
   *Meu Drive → Buscador de Clientes* (junto com o histórico e a trava de gastos).

---

## Jeito alternativo: no seu computador

### 1. Instalar (uma vez só)

1. Instale o **Python 3.10 ou mais novo**: <https://www.python.org/downloads/>
   (no Windows, marque a opção **"Add Python to PATH"** na instalação).
2. Baixe esta pasta (botão verde **Code → Download ZIP** no GitHub) e descompacte.
3. (Opcional, para gerar a planilha `.xlsx`) abra o terminal na pasta e rode:
   ```
   pip install -r requirements.txt
   ```
   Sem isso o programa funciona do mesmo jeito; só não gera o `.xlsx`, apenas o `.html` e o `.csv`.

### 2. Usar

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

### Chave do Google (recomendado) — sem gastar nada

Para usar o Google Maps é preciso cadastrar um cartão no Google Cloud, mesmo usando só a parte
grátis. Siga nesta ordem:

1. **Cadastrar o cartão (teste gratuito):** <https://console.cloud.google.com/freetrial>
   Enquanto você estiver no teste gratuito, o Google **não cobra nada** a não ser que você clique
   em **"Ativar conta completa"** (ou *Upgrade*). **Não clique nisso.**
2. **Ativar a API de lugares:** <https://console.cloud.google.com/apis/library/places.googleapis.com>
   → botão **Ativar** (é a "Places API (New)").
3. **Criar a chave:** <https://console.cloud.google.com/apis/credentials> → **Criar credenciais →
   Chave de API**. Depois clique na chave criada → **Restrições de API → Restringir chave →**
   marque só **Places API (New)** → Salvar. Assim, se alguém pegar sua chave, não consegue usar
   em outros serviços.
4. **Colocar a chave no programa:** no Colab, no secret `GOOGLE_MAPS_API_KEY` (veja acima); no
   computador, num arquivo `chave_google.txt` nesta pasta. **Nunca publique a chave em lugar nenhum.**
5. **Alerta de gastos (recomendado):** <https://console.cloud.google.com/billing/budgets> →
   **Criar orçamento** de R$ 1 com alerta por e-mail. Isso não bloqueia nada, só avisa.
6. **Limite no próprio Google (opcional):** <https://console.cloud.google.com/google/maps-apis/quotas>
   → escolha **Places API (New)** → edite o limite de **SearchTextRequest** (por dia, se aparecer)
   para um número pequeno, como 30.

**Como o programa garante que você não gaste:** o Google dá **1.000 consultas grátis por mês**
para esse tipo de busca. O programa conta cada consulta e **para sozinho em 900 por mês** (dá para
mudar com `--limite-mensal`), voltando a buscar no mês seguinte. Cada consulta traz até 20
negócios, então são até ~18.000 negócios grátis por mês. Cada nicho em cada cidade usa no máximo
3 consultas.

> ⚠️ A contagem fica salva na pasta de resultados. Se você usar o programa no computador **e** no
> Colab, cada um conta separado; nesse caso use `--limite-mensal 450` em cada um, ou configure o
> limite do item 6. Os preços do Google podem mudar: confira em
> <https://developers.google.com/maps/billing-and-pricing/pricing>.

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

Sem dependências obrigatórias (só a biblioteca padrão do Python). Depois de mudar algo em
`buscador_clientes/`, regenere o caderno do Colab com `python ferramentas/gerar_notebook.py`. Testes:

```
pip install pytest openpyxl
python -m pytest
```
