"""Gera Buscador_de_Clientes.ipynb, a versão do programa que roda no Google Colab.

O código do programa vai embutido no caderno, então ele funciona sem baixar nada.
Rode de novo sempre que mudar algo em buscador_clientes/:

    python ferramentas/gerar_notebook.py
"""

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "Buscador_de_Clientes.ipynb"

INTRO = """# 🎬 Buscador de clientes para edição de vídeo

Procura negócios no Google Maps que podem comprar seus pacotes de edição de vídeo e monta uma lista
com telefone, Instagram, WhatsApp e uma nota para cada cliente.

**Como usar (é só clicar):**
1. *(Uma vez só)* Clique na chave 🔑 na barra da esquerda → **Adicionar novo secret** →
   nome `GOOGLE_MAPS_API_KEY`, valor = sua chave do Google → ative o acesso do notebook.
   Sem a chave ele usa o OpenStreetMap, que é grátis mas tem menos telefones.
2. Clique no ▶ do **Passo 1**.
3. Preencha a cidade e os nichos no **Passo 2** e clique no ▶. Na primeira vez o Google pede
   permissão para salvar no seu Google Drive: aceite, assim o histórico e a trava de gastos ficam guardados.

A trava de gastos para as buscas no Google em 900 por mês, abaixo da cota grátis de 1.000."""

PASSO_2 = '''# @title Passo 2: buscar clientes
cidade = "Campinas, SP"  # @param {type:"string"}
nichos = "academia, estetica, imobiliaria, restaurante, barbearia"  # @param {type:"string"}
pontuacao_minima = 0  # @param {type:"slider", min:0, max:100, step:5}
fonte = "auto"  # @param ["auto", "google", "osm", "ambas"]
salvar_no_google_drive = True  # @param {type:"boolean"}
# Nichos prontos: academia, personal, estetica, salao, barbearia, imobiliaria, restaurante,
# hamburgueria, cafeteria, bar, dentista, clinica, advogado, loja_roupas, concessionaria, escola,
# curso, autoescola, petshop, hotel, eventos, fotografo, igreja, tatuagem, agencia, construtora,
# padaria, todos — ou qualquer outro termo (ex.: nutricionista).
# Várias cidades: separe com ";" (ex.: "Campinas, SP; Valinhos, SP").

import os
from pathlib import Path

from IPython.display import HTML, display

try:
    from google.colab import userdata
    os.environ["GOOGLE_MAPS_API_KEY"] = userdata.get("GOOGLE_MAPS_API_KEY") or ""
except Exception:
    os.environ.pop("GOOGLE_MAPS_API_KEY", None)
    print("Chave do Google não encontrada nos secrets (🔑): usando o OpenStreetMap.\\n")

pasta = Path("/content/resultados")
if salvar_no_google_drive:
    from google.colab import drive
    drive.mount("/content/drive")
    pasta = Path("/content/drive/MyDrive/Buscador de Clientes")

from buscador_clientes.cli import main

main(["--cidade", cidade, "--nichos", nichos, "--fonte", fonte,
      "--min-pontuacao", str(pontuacao_minima), "--saida", str(pasta)])

paginas = sorted(pasta.glob("clientes_*.html"), key=lambda p: p.stat().st_mtime)
if paginas:
    display(HTML(paginas[-1].read_text(encoding="utf-8")))
    planilha = paginas[-1].with_suffix(".xlsx")
    if planilha.exists():
        from google.colab import files
        files.download(str(planilha))'''


def celula_codigo(codigo, esconder=True):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"cellView": "form"} if esconder else {},
        "outputs": [],
        "source": codigo.splitlines(keepends=True),
    }


def gerar():
    arquivos = {
        f"buscador_clientes/{p.name}": p.read_text(encoding="utf-8")
        for p in sorted((RAIZ / "buscador_clientes").glob("*.py"))
    }
    arquivos["mensagem.txt"] = (RAIZ / "mensagem.txt").read_text(encoding="utf-8")
    passo_1 = (
        "# @title Passo 1: preparar o programa (só clicar ▶)\n"
        "# Para mudar a mensagem do WhatsApp, edite /content/mensagem.txt depois deste passo.\n"
        "from pathlib import Path\n\n"
        f"ARQUIVOS = {json.dumps(arquivos, ensure_ascii=False, indent=0)}\n\n"
        "for caminho, conteudo in ARQUIVOS.items():\n"
        "    Path(caminho).parent.mkdir(parents=True, exist_ok=True)\n"
        "    Path(caminho).write_text(conteudo, encoding=\"utf-8\")\n"
        "print(\"Programa pronto! Agora vá para o Passo 2.\")"
    )
    caderno = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": INTRO.splitlines(keepends=True)},
            celula_codigo(passo_1),
            celula_codigo(PASSO_2),
        ],
        "metadata": {
            "colab": {"provenance": [], "toc_visible": False},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }
    return json.dumps(caderno, ensure_ascii=False, indent=1) + "\n"


if __name__ == "__main__":
    DESTINO.write_text(gerar(), encoding="utf-8")
    print(f"Gerado: {DESTINO}")
