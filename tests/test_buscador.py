import csv
from unittest import mock

from buscador_clientes import analise, cli, google_places, openstreetmap
from buscador_clientes.modelo import Lead

HTML_SITE = """
<a href="https://www.instagram.com/academiaforte/">Insta</a>
<a href="https://www.facebook.com/sharer/sharer.php?u=x">share</a>
<a href="https://facebook.com/academiaforte">Face</a>
<a href="https://wa.me/5519998765432">Zap</a>
<img src="logo@2x.png"> contato@academiaforte.com.br
"""


def test_extrair_contatos():
    achados = analise.extrair_contatos(HTML_SITE)
    assert achados["instagram"] == "https://www.instagram.com/academiaforte"
    assert achados["facebook"] == "https://facebook.com/academiaforte"
    assert achados["whatsapp"] == "5519998765432"
    assert achados["email"] == "contato@academiaforte.com.br"
    assert "youtube" not in achados


def test_telefones():
    assert analise.normalizar_telefone_br("(19) 99876-5432") == "5519998765432"
    assert analise.normalizar_telefone_br("+55 19 3232-1234") == "551932321234"
    assert analise.normalizar_telefone_br("019 99876-5432") == "5519998765432"
    assert analise.normalizar_telefone_br("123") == ""
    assert analise.eh_celular("(19) 99876-5432")
    assert not analise.eh_celular("(19) 3232-1234")


def test_link_whatsapp_so_para_celular():
    fixo = Lead(nome="Padaria", nicho="padaria", fonte="x", telefone="(19) 3232-1234")
    assert analise.link_whatsapp(fixo, "Oi {nome}") == ""
    cel = Lead(nome="Barbearia do Zé", nicho="barbearia", fonte="x", telefone="(19) 99876-5432")
    assert analise.link_whatsapp(cel, "Oi {nome}") == "https://wa.me/5519998765432?text=Oi%20Barbearia%20do%20Z%C3%A9"


def test_pontuacao_ordena_bons_leads_primeiro():
    bom = Lead(nome="A", nicho="academia", fonte="x", telefone="(19) 99876-5432",
               instagram="https://instagram.com/a", site="a.com", avaliacoes=300, nota=4.8)
    fraco = Lead(nome="B", nicho="padaria", fonte="x")
    analise.pontuar(bom)
    analise.pontuar(fraco)
    assert bom.pontuacao > 70
    assert fraco.pontuacao <= 20
    assert "sem contato encontrado" in fraco.motivos


def test_google_places_pagina_e_ignora_fechados():
    paginas = [
        {"places": [{"displayName": {"text": "Academia Forte"}, "nationalPhoneNumber": "(19) 99876-5432",
                     "websiteUri": "https://forte.com", "rating": 4.7, "userRatingCount": 120,
                     "businessStatus": "OPERATIONAL"}],
         "nextPageToken": "abc"},
        {"places": [{"displayName": {"text": "Academia Fechada"}, "businessStatus": "CLOSED_PERMANENTLY"},
                    {"displayName": {"text": "Academia Dois"}}]},
    ]
    with mock.patch.object(google_places, "post_json", side_effect=paginas) as post, \
         mock.patch.object(google_places.time, "sleep"):
        leads = google_places.buscar("CHAVE", "academia", "Campinas, SP", "academia", log=lambda *_: None)
    assert [l.nome for l in leads] == ["Academia Forte", "Academia Dois"]
    assert post.call_args_list[1].args[1]["pageToken"] == "abc"
    assert post.call_args_list[0].args[2]["X-Goog-Api-Key"] == "CHAVE"


def test_openstreetmap():
    nominatim = [{"osm_type": "node", "osm_id": 1}, {"osm_type": "relation", "osm_id": 298640}]
    overpass = {"elements": [
        {"type": "node", "lat": -22.9, "lon": -47.06,
         "tags": {"name": "Barbearia Navalha", "shop": "hairdresser", "hairdresser": "barber",
                  "phone": "+55 19 99876-5432", "addr:street": "Rua A", "addr:housenumber": "10"}},
        {"type": "way", "center": {"lat": -22.8, "lon": -47.0},
         "tags": {"name": "Smart Fit", "leisure": "fitness_centre", "website": "https://smartfit.com.br"}},
    ]}
    with mock.patch.object(openstreetmap, "get_json", return_value=nominatim), \
         mock.patch.object(openstreetmap, "post_form", return_value=overpass) as post, \
         mock.patch.object(openstreetmap.time, "sleep"):
        leads = openstreetmap.buscar("Campinas, SP", ["academia", "barbearia", "salao"], log=lambda *_: None)
    consulta = post.call_args.args[1]["data"]
    assert "area(3600298640)" in consulta
    assert '["leisure"="fitness_centre"]' in consulta
    assert [(l.nome, l.nicho) for l in leads] == [("Barbearia Navalha", "barbearia"), ("Smart Fit", "academia")]
    assert leads[0].endereco == "Rua A, 10"


def test_programa_completo(tmp_path):
    lugares = {"places": [
        {"displayName": {"text": "Studio Bela"}, "nationalPhoneNumber": "(11) 98888-7777",
         "websiteUri": "https://studiobela.com.br", "userRatingCount": 80, "rating": 4.9},
        {"displayName": {"text": "Studio Bela"}, "nationalPhoneNumber": "(11) 98888-7777"},  # repetido
    ]}
    with mock.patch.object(google_places, "post_json", return_value=lugares), \
         mock.patch.object(analise, "get_texto", return_value=HTML_SITE):
        codigo = cli.main(["--cidade", "São Paulo, SP", "--nichos", "estetica", "--chave-google", "X",
                           "--saida", str(tmp_path)])
        assert codigo == 0
        # Segunda busca igual não repete quem já apareceu.
        cli.main(["--cidade", "São Paulo, SP", "--nichos", "estetica", "--chave-google", "X",
                  "--saida", str(tmp_path)])

    csvs = list(tmp_path.glob("clientes_*.csv"))
    assert len(csvs) == 1
    with open(csvs[0], encoding="utf-8-sig") as f:
        linhas = list(csv.DictReader(f, delimiter=";"))
    assert len(linhas) == 1
    assert linhas[0]["Nome"] == "Studio Bela"
    assert linhas[0]["Instagram"] == "https://www.instagram.com/academiaforte"
    assert linhas[0]["Chamar no WhatsApp"].startswith("https://wa.me/5519998765432")
    assert list(tmp_path.glob("clientes_*.html"))


def test_trava_de_gastos_para_no_limite(tmp_path):
    pagina = {"places": [{"displayName": {"text": "Loja"}}], "nextPageToken": "t"}
    contador = google_places.ContadorUso(tmp_path / "uso.json", limite=2)
    with mock.patch.object(google_places, "post_json", return_value=pagina) as post, \
         mock.patch.object(google_places.time, "sleep"):
        try:
            google_places.buscar("X", "loja", "Recife", "loja", log=lambda *_: None, contador=contador)
            assert False, "devia ter parado no limite"
        except google_places.LimiteMensalAtingido:
            pass
    assert post.call_count == 2
    # O limite vale para o mês todo, mesmo fechando e abrindo o programa de novo.
    assert google_places.ContadorUso(tmp_path / "uso.json", limite=2).usados == 2


def test_programa_respeita_limite_mensal(tmp_path, capsys):
    with mock.patch.object(google_places, "post_json") as post:
        cli.main(["--cidade", "Recife, PE", "--chave-google", "X", "--limite-mensal", "0", "--saida", str(tmp_path)])
    post.assert_not_called()
    assert "Limite de 0 consultas" in capsys.readouterr().out


def test_notebook_do_colab_esta_atualizado():
    from ferramentas import gerar_notebook

    assert gerar_notebook.DESTINO.read_text(encoding="utf-8") == gerar_notebook.gerar(), (
        "Rode: python ferramentas/gerar_notebook.py"
    )
