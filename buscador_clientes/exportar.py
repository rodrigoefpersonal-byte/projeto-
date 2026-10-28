"""Salva a lista de clientes em CSV (abre no Excel), Excel (.xlsx) e uma página HTML."""

import csv
import html
from pathlib import Path

from .nichos import NICHOS

COLUNAS = [
    ("pontuacao", "Pontuação"),
    ("nome", "Nome"),
    ("nicho", "Nicho"),
    ("telefone", "Telefone"),
    ("link_whatsapp", "Chamar no WhatsApp"),
    ("instagram", "Instagram"),
    ("email", "E-mail"),
    ("site", "Site"),
    ("facebook", "Facebook"),
    ("youtube", "YouTube"),
    ("tiktok", "TikTok"),
    ("nota", "Nota"),
    ("avaliacoes", "Avaliações"),
    ("endereco", "Endereço"),
    ("cidade", "Cidade"),
    ("link_mapa", "Ver no mapa"),
    ("motivos", "Por que é um bom lead"),
    ("fonte", "Fonte"),
]
LINKS = {"link_whatsapp", "instagram", "site", "facebook", "youtube", "tiktok", "link_mapa"}


def _valor(lead, campo):
    v = getattr(lead, campo)
    if campo == "motivos":
        return "; ".join(v)
    if campo == "nicho":
        return NICHOS.get(v, {}).get("busca", v)
    return "" if v is None else v


def salvar_csv(leads, caminho):
    # ";" e utf-8-sig fazem o Excel em português abrir o arquivo com acentos e colunas certas.
    with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([titulo for _, titulo in COLUNAS])
        for lead in leads:
            w.writerow([_valor(lead, c) for c, _ in COLUNAS])


def salvar_xlsx(leads, caminho):
    """Gera a planilha Excel se a biblioteca openpyxl estiver instalada. Devolve True se salvou."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        return False
    wb = Workbook()
    ws = wb.active
    ws.title = "Clientes"
    ws.append([titulo for _, titulo in COLUNAS])
    for cel in ws[1]:
        cel.font = Font(bold=True, color="FFFFFF")
        cel.fill = PatternFill("solid", fgColor="4F46E5")
    for lead in leads:
        ws.append([_valor(lead, c) for c, _ in COLUNAS])
        linha = ws.max_row
        for i, (campo, _) in enumerate(COLUNAS, start=1):
            url = getattr(lead, campo)
            if campo in LINKS and isinstance(url, str) and url.startswith("http"):
                cel = ws.cell(row=linha, column=i)
                cel.hyperlink = url
                cel.value = "Abrir conversa" if campo == "link_whatsapp" else url
                cel.font = Font(color="0563C1", underline="single")
    larguras = {"Nome": 35, "Endereço": 45, "Por que é um bom lead": 60, "Chamar no WhatsApp": 18}
    for i, (_, titulo) in enumerate(COLUNAS, start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = larguras.get(titulo, 20)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    wb.save(caminho)
    return True


def _link(url, texto=None):
    if not url:
        return ""
    if not url.startswith("http"):
        url = "https://" + url
    return f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(texto or url)}</a>'


def salvar_html(leads, caminho, titulo):
    linhas = []
    for l in leads:
        cor = "alta" if l.pontuacao >= 60 else "media" if l.pontuacao >= 40 else "baixa"
        redes = " ".join(
            filter(None, [
                _link(l.instagram, "Instagram"), _link(l.facebook, "Facebook"),
                _link(l.youtube, "YouTube"), _link(l.tiktok, "TikTok"), _link(l.site, "Site"),
            ])
        )
        zap = f'<a class="zap" href="{html.escape(l.link_whatsapp)}" target="_blank">WhatsApp</a>' if l.link_whatsapp else ""
        nota = f"{l.nota:.1f} ★ ({l.avaliacoes or 0})" if l.nota else ""
        linhas.append(
            f"<tr><td><span class='nota {cor}'>{l.pontuacao}</span></td>"
            f"<td><strong>{html.escape(l.nome)}</strong><br><small>{html.escape(_valor(l, 'nicho'))}</small></td>"
            f"<td>{html.escape(l.telefone)}<br>{zap}</td>"
            f"<td>{redes}<br><small>{html.escape(l.email)}</small></td>"
            f"<td>{nota}</td>"
            f"<td><small>{html.escape(l.endereco)}</small><br>{_link(l.link_mapa, 'Ver no mapa')}</td>"
            f"<td><small>{html.escape('; '.join(l.motivos))}</small></td></tr>"
        )
    pagina = f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titulo)}</title>
<style>
body{{font-family:system-ui,sans-serif;margin:0;padding:16px;background:#f6f7fb;color:#1f2330}}
h1{{font-size:1.3rem}} input{{padding:8px;width:100%;max-width:400px;margin-bottom:12px;border:1px solid #ccc;border-radius:6px}}
td:nth-child(3){{white-space:nowrap}} .tabela{{overflow-x:auto}} table{{border-collapse:collapse;width:100%;background:#fff}}
th,td{{padding:8px;border-bottom:1px solid #e5e7eb;text-align:left;vertical-align:top;font-size:.9rem}}
th{{background:#4f46e5;color:#fff;position:sticky;top:0}} a{{color:#4338ca;margin-right:6px}}
.nota{{display:inline-block;min-width:32px;text-align:center;padding:4px;border-radius:6px;font-weight:bold;color:#fff}}
.alta{{background:#16a34a}} .media{{background:#d97706}} .baixa{{background:#9ca3af}}
.zap{{display:inline-block;margin-top:4px;background:#25d366;color:#fff;padding:3px 8px;border-radius:4px;text-decoration:none}}
</style></head><body>
<h1>{html.escape(titulo)} — {len(leads)} clientes</h1>
<input id="filtro" placeholder="Filtrar por nome, nicho, bairro..." oninput="filtrar(this.value)">
<div class="tabela"><table><thead><tr><th>Nota</th><th>Negócio</th><th>Telefone</th><th>Redes / e-mail</th>
<th>Google</th><th>Endereço</th><th>Por que é um bom lead</th></tr></thead><tbody>
{''.join(linhas)}
</tbody></table></div>
<script>function filtrar(t){{t=t.toLowerCase();document.querySelectorAll('tbody tr').forEach(r=>{{r.style.display=r.innerText.toLowerCase().includes(t)?'':'none'}})}}</script>
</body></html>"""
    Path(caminho).write_text(pagina, encoding="utf-8")
