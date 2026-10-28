"""Programa principal: python buscar_clientes.py --cidade "Campinas, SP" --nichos academia,restaurante"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from . import exportar, google_places, openstreetmap
from .analise import analisar_sites, link_whatsapp, pontuar
from .http import ErroHTTP
from .nichos import NICHOS, NICHOS_PADRAO, resolver_nichos

PASTA_PROGRAMA = Path(__file__).resolve().parent.parent
MENSAGEM_PADRAO = (
    "Olá, {nome}! Tudo bem? Vi o trabalho de vocês e acho que vídeos bem editados "
    "podem trazer muito mais clientes pelo Instagram e TikTok. Eu trabalho com pacotes "
    "de edição de vídeo (Reels, anúncios e vídeos institucionais). Posso te mandar alguns exemplos?"
)


def ler_chave_google(valor_cli):
    if valor_cli:
        return valor_cli.strip()
    if os.environ.get("GOOGLE_MAPS_API_KEY"):
        return os.environ["GOOGLE_MAPS_API_KEY"].strip()
    arquivo = PASTA_PROGRAMA / "chave_google.txt"
    if arquivo.exists():
        return arquivo.read_text(encoding="utf-8").strip()
    return ""


def ler_mensagem(caminho):
    arquivo = Path(caminho) if caminho else PASTA_PROGRAMA / "mensagem.txt"
    if arquivo.exists():
        texto = arquivo.read_text(encoding="utf-8").strip()
        if texto:
            return texto
    return MENSAGEM_PADRAO


def perguntar(args):
    """Modo passo a passo para quem não quer digitar parâmetros."""
    print("=== Buscador de clientes para edição de vídeo ===\n")
    args.cidade = input('Em qual cidade procurar? (ex.: "Campinas, SP" — várias separadas por ";")\n> ').strip()
    print("\nNichos disponíveis:")
    print("  " + ", ".join(NICHOS))
    print(f"(Enter = {', '.join(NICHOS_PADRAO)}; 'todos' = todos; pode digitar outro termo, ex.: nutricionista)")
    args.nichos = input("> ").strip()
    minimo = input("\nPontuação mínima para entrar na lista? (0 a 100, Enter = 0)\n> ").strip()
    args.min_pontuacao = int(minimo) if minimo.isdigit() else 0
    print()


def criar_parser():
    p = argparse.ArgumentParser(
        description="Encontra negócios no Google Maps / OpenStreetMap que podem comprar pacotes de edição de vídeo."
    )
    p.add_argument("--cidade", help='Cidade(s), ex.: "Campinas, SP". Várias separadas por ";"')
    p.add_argument("--nichos", help=f"Separados por vírgula. Disponíveis: {', '.join(NICHOS)} ou 'todos'")
    p.add_argument("--fonte", choices=["auto", "google", "osm", "ambas"], default="auto",
                   help="auto = Google se houver chave, senão OpenStreetMap (padrão)")
    p.add_argument("--chave-google", help="Chave da Places API (ou use chave_google.txt / GOOGLE_MAPS_API_KEY)")
    p.add_argument("--max-por-busca", type=int, default=60, help="Máximo de resultados do Google por nicho (até 60)")
    p.add_argument("--limite-mensal", type=int, default=google_places.LIMITE_MENSAL_PADRAO,
                   help="Máximo de consultas ao Google por mês, para ficar na cota grátis (padrão: 900)")
    p.add_argument("--min-pontuacao", type=int, default=0, help="Só exporta leads com pontuação >= este valor")
    p.add_argument("--sem-analise-site", action="store_true", help="Não visita os sites (mais rápido, menos dados)")
    p.add_argument("--mensagem", help="Arquivo .txt com a mensagem do WhatsApp (use {nome} para o nome do negócio)")
    p.add_argument("--saida", default=str(PASTA_PROGRAMA / "resultados"), help="Pasta onde salvar os arquivos")
    p.add_argument("--incluir-repetidos", action="store_true",
                   help="Inclui negócios que já apareceram em buscas anteriores")
    return p


def carregar_historico(pasta):
    arquivo = pasta / "historico.txt"
    if not arquivo.exists():
        return set()
    return set(arquivo.read_text(encoding="utf-8").splitlines())


def salvar_historico(pasta, leads):
    with open(pasta / "historico.txt", "a", encoding="utf-8") as f:
        for lead in leads:
            f.write("|".join(lead.chave()) + "\n")


def coletar(args, cidades, nichos, chave, pasta):
    usar_google = args.fonte in ("google", "ambas") or (args.fonte == "auto" and chave)
    usar_osm = args.fonte in ("osm", "ambas") or (args.fonte == "auto" and not chave)
    if usar_google and not chave:
        sys.exit("Para usar o Google Maps é preciso uma chave de API. Veja o README (seção 'Chave do Google').")
    if args.fonte == "auto" and not chave:
        print("Sem chave do Google: usando o OpenStreetMap (grátis). Para mais resultados, veja o README.\n")

    contador = google_places.ContadorUso(pasta / "uso_google.json", args.limite_mensal)
    leads = []
    for cidade in cidades:
        print(f"Procurando em {cidade}...")
        if usar_google:
            for n in nichos:
                try:
                    leads += google_places.buscar(chave, NICHOS[n]["busca"], cidade, n, args.max_por_busca,
                                                  contador=contador)
                except ErroHTTP as e:
                    print(f"  Erro no Google Maps ({n}): {e}")
                except google_places.LimiteMensalAtingido as e:
                    print(f"  {e}")
                    usar_google = False
                    break
        if usar_osm:
            try:
                leads += openstreetmap.buscar(cidade, nichos)
            except ErroHTTP as e:
                print(f"  Erro no OpenStreetMap: {e}")
    if chave and args.fonte != "osm":
        print(f"Consultas ao Google neste mês: {contador.usados} de {contador.limite} (cota grátis).\n")
    return leads


def main(argv=None):
    args = criar_parser().parse_args(argv)
    if not args.cidade:
        perguntar(args)
    cidades = [c.strip() for c in (args.cidade or "").split(";") if c.strip()]
    if not cidades:
        print("Informe pelo menos uma cidade.")
        return 1
    nichos = resolver_nichos((args.nichos or "").split(",") if args.nichos else [])
    chave = ler_chave_google(args.chave_google)

    pasta = Path(args.saida)
    pasta.mkdir(parents=True, exist_ok=True)
    leads = coletar(args, cidades, nichos, chave, pasta)

    unicos = {}
    for lead in leads:
        unicos.setdefault(lead.chave(), lead)
    leads = [l for l in unicos.values() if l.nome]

    if not args.incluir_repetidos:
        historico = carregar_historico(pasta)
        antes = len(leads)
        leads = [l for l in leads if "|".join(l.chave()) not in historico]
        if antes - len(leads):
            print(f"{antes - len(leads)} já tinham aparecido em buscas anteriores e foram ignorados "
                  "(use --incluir-repetidos para mostrar).")

    if not leads:
        print("Nenhum cliente novo encontrado. Tente outra cidade, outros nichos ou --fonte ambas.")
        return 0

    if not args.sem_analise_site:
        analisar_sites(leads)

    mensagem = ler_mensagem(args.mensagem)
    for lead in leads:
        pontuar(lead)
        lead.link_whatsapp = link_whatsapp(lead, mensagem)
    leads = [l for l in leads if l.pontuacao >= args.min_pontuacao]
    leads.sort(key=lambda l: (-l.pontuacao, -(l.avaliacoes or 0)))
    if not leads:
        print("Nenhum cliente passou da pontuação mínima. Diminua --min-pontuacao.")
        return 0

    nome_base = f"clientes_{datetime.now():%Y-%m-%d_%H%M}"
    salvar_historico(pasta, leads)
    exportar.salvar_csv(leads, pasta / f"{nome_base}.csv")
    arquivos = [f"{nome_base}.csv"]
    if exportar.salvar_xlsx(leads, pasta / f"{nome_base}.xlsx"):
        arquivos.append(f"{nome_base}.xlsx")
    exportar.salvar_html(leads, pasta / f"{nome_base}.html", f"Clientes em {', '.join(cidades)}")
    arquivos.append(f"{nome_base}.html")

    com_zap = sum(1 for l in leads if l.link_whatsapp)
    print(f"\nPronto! {len(leads)} clientes encontrados ({com_zap} com link direto para o WhatsApp).")
    print("Melhores leads:")
    for l in leads[:10]:
        print(f"  [{l.pontuacao:3d}] {l.nome} — {l.telefone or l.instagram or l.email or 'sem contato'}")
    print(f"\nArquivos salvos em {pasta}:")
    for a in arquivos:
        print(f"  - {a}")
    return 0
