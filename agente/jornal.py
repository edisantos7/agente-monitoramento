"""
jornal.py — a versão "jornal" do relatório: uma página HTML que abre no browser.

Recebe os mesmos dados que relatorio.gerar_markdown e devolve uma página completa
(com o CSS lá dentro, não precisa de mais ficheiros). As fotografias vêm dos sites
dos jornais, por isso só aparecem com internet.
"""

from datetime import datetime
from html import escape

from .analise import avaliar
from .noticias import selecionar_do_dia
from .relatorio import titulo_secao

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def gerar_html(leituras, fonte, agora=None, noticias=None, fonte_noticias=None, avisos=(), resumos=True):
    """
    `resumos=False` deixa só títulos, fotografias e links — é a versão para o site público,
    porque o texto dos resumos pertence aos jornais.
    """
    agora = agora or datetime.now()
    destaques = selecionar_do_dia(noticias, agora) if noticias is not None else {}
    data_extenso = f"{DIAS[agora.weekday()].capitalize()}, {agora.day} de {MESES[agora.month - 1]} de {agora.year}"

    navegacao = "".join(f'<a href="#{s}">{escape(titulo_secao(s))}</a>' for s in destaques)
    secoes = "".join(_secao(s, d, resumos) for s, d in destaques.items())
    avisos_html = "".join(f"<li>{escape(a)}</li>" for a in avisos)

    return f"""<!doctype html>
<html lang="pt-PT">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>O Agente — {agora:%d/%m/%Y}</title>
<style>{CSS}</style>
</head>
<body>
<header class="cabecalho">
  <div class="faixa"><span>{escape(data_extenso)}</span><span>Edição das {agora:%H:%M}</span></div>
  <h1 class="nome">O Agente</h1>
  <p class="lema">As notícias do dia, recolhidas automaticamente em vários jornais</p>
  <nav class="nav">{navegacao}</nav>
</header>
{_tempo(leituras, fonte)}
<main>
{secoes or '<p class="vazio">Sem notícias nesta edição.</p>'}
</main>
<footer class="rodape">
  <p>Notícias: {escape(fonte_noticias or "—")} · Meteorologia: {escape(fonte)}</p>
  {f'<details><summary>Avisos da recolha ({len(avisos)})</summary><ul>{avisos_html}</ul></details>' if avisos else ''}
  <p>Cada notícia leva ao site do jornal que a publicou. Gerado em {agora:%d/%m/%Y às %H:%M:%S}.</p>
</footer>
</body>
</html>
"""


def _secao(secao, destaque, resumos=True):
    itens = destaque["itens"]
    cabecalho = f'<h2 class="titulo-secao">{escape(titulo_secao(secao))}</h2>'
    if not itens:
        return f'<section class="secao" id="{secao}">{cabecalho}<p class="vazio">Sem notícias disponíveis.</p></section>'

    nota = "" if destaque["de_hoje"] else '<p class="nota">Ainda não há notícias de hoje nesta secção — a mostrar as mais recentes.</p>'
    manchete, *outras = itens
    cartoes = "".join(_cartao(n) for n in outras)
    return f"""<section class="secao" id="{secao}">
  {cabecalho}{nota}
  <article class="manchete">
    {_foto(manchete, "foto-grande")}
    <div class="texto">
      <span class="etiqueta">Manchete</span>
      <h3><a href="{escape(manchete['link'])}" target="_blank" rel="noopener">{escape(manchete['titulo'])}</a></h3>
      {f"<p class='resumo'>{escape(manchete['resumo'])}</p>" if resumos and manchete['resumo'] else ''}
      {_meta(manchete)}
    </div>
  </article>
  {f'<div class="grelha">{cartoes}</div>' if cartoes else ''}
</section>
"""


def _cartao(noticia):
    return f"""<article class="cartao">
  {_foto(noticia, "foto")}
  <h4><a href="{escape(noticia['link'])}" target="_blank" rel="noopener">{escape(noticia['titulo'])}</a></h4>
  {_meta(noticia)}
</article>"""


def _foto(noticia, classe):
    if not noticia.get("imagem"):
        return ""
    return (
        f'<a class="{classe}" href="{escape(noticia["link"])}" target="_blank" rel="noopener" tabindex="-1">'
        f'<img src="{escape(noticia["imagem"])}" alt="" loading="lazy" referrerpolicy="no-referrer" '
        f"onerror=\"this.parentElement.remove()\"></a>"
    )


def _meta(noticia):
    partes = [f'<strong>{escape(noticia["fonte"])}</strong>', f'{noticia["data"]:%H:%M}']
    if noticia.get("tambem_em"):
        links = ", ".join(
            f'<a href="{escape(o["link"])}" target="_blank" rel="noopener">{escape(o["fonte"])}</a>'
            for o in noticia["tambem_em"]
        )
        partes.append(f'<span class="tambem">também em {links}</span>')
    return f'<p class="meta">{" · ".join(partes)}</p>'


def _tempo(leituras, fonte):
    if not leituras:
        return ""
    locais = "".join(
        f'<li><span class="local">{escape(l["local"])}</span>'
        f'<span class="graus">{round(l["temperatura"])}°</span>'
        f'<span class="extra">💨 {round(l["vento"])} km/h · 💧 {round(l["humidade"])}%</span></li>'
        for l in leituras
    )
    alertas = "".join(f'<li>⚠️ <strong>{escape(a["local"])}</strong> — {escape(a["mensagem"])}</li>' for a in avaliar(leituras))
    return f"""<section class="tempo" aria-label="Meteorologia">
  <h2>O tempo agora</h2>
  <ul class="locais">{locais}</ul>
  {f'<ul class="alertas">{alertas}</ul>' if alertas else ''}
</section>"""


CSS = """
:root {
  --papel: #f7f4ee; --tinta: #1d1b18; --suave: #6b655c; --linha: #d9d2c5;
  --destaque: #a4161a; --cartao: #fffdf9; --alerta-fundo: #fbe9e7;
}
@media (prefers-color-scheme: dark) {
  :root {
    --papel: #161513; --tinta: #ece7de; --suave: #a39c90; --linha: #3a3631;
    --destaque: #ff6b6b; --cartao: #1f1d1a; --alerta-fundo: #3a1f1d;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--papel); color: var(--tinta);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
a { color: inherit; text-decoration: none; }
a:hover { text-decoration: underline; }
a:focus-visible { outline: 2px solid var(--destaque); outline-offset: 2px; }
.cabecalho, .tempo, main, .rodape { max-width: 1150px; margin: 0 auto; padding: 0 16px; }

.cabecalho { text-align: center; padding-top: 12px; }
.faixa {
  display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap;
  font-size: 13px; color: var(--suave);
  border-bottom: 1px solid var(--linha); padding-bottom: 8px;
}
.nome {
  font-family: Georgia, "Times New Roman", serif; font-size: clamp(44px, 9vw, 88px);
  line-height: 1; margin: 18px 0 6px; letter-spacing: -1px;
}
.lema { margin: 0 0 14px; color: var(--suave); font-style: italic; font-family: Georgia, serif; }
.nav {
  display: flex; justify-content: center; flex-wrap: wrap; gap: 4px 18px;
  border-top: 3px double var(--tinta); border-bottom: 3px double var(--tinta); padding: 10px 0;
  font-weight: 600; font-size: 14px;
}

.tempo { margin-top: 18px; }
.tempo h2 { font-size: 12px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--suave); margin: 0 0 8px; }
.locais { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 8px; }
.locais li {
  background: var(--cartao); border: 1px solid var(--linha); border-radius: 6px; padding: 8px 12px;
  display: grid; grid-template-columns: 1fr auto; align-items: baseline;
}
.local { font-weight: 600; }
.graus { font-family: Georgia, serif; font-size: 26px; grid-row: span 2; }
.extra { font-size: 12px; color: var(--suave); }
.alertas { list-style: none; padding: 8px 12px; margin: 8px 0 0; background: var(--alerta-fundo); border-radius: 6px; font-size: 14px; }

.secao { margin-top: 36px; }
.titulo-secao {
  font-family: Georgia, serif; font-size: 26px; margin: 0 0 16px; padding-bottom: 6px;
  border-bottom: 2px solid var(--tinta);
}
.nota { color: var(--suave); font-style: italic; font-size: 14px; margin-top: -8px; }
.manchete { display: grid; gap: 20px; grid-template-columns: 1fr; margin-bottom: 20px; }
@media (min-width: 760px) { .manchete:has(.foto-grande) { grid-template-columns: 3fr 2fr; } }
.foto-grande img, .foto img { width: 100%; display: block; object-fit: cover; border-radius: 4px; background: var(--linha); }
.foto-grande img { aspect-ratio: 16 / 9; }
.foto img { aspect-ratio: 16 / 9; margin-bottom: 8px; }
.etiqueta {
  display: inline-block; background: var(--destaque); color: #fff; font-size: 11px; font-weight: 700;
  text-transform: uppercase; letter-spacing: 1px; padding: 2px 8px; border-radius: 2px;
}
.manchete h3 { font-family: Georgia, serif; font-size: clamp(24px, 3.4vw, 34px); line-height: 1.15; margin: 10px 0; }
.resumo { font-size: 17px; margin: 0 0 10px; }
.meta { font-size: 13px; color: var(--suave); margin: 0; }
.meta .tambem a { text-decoration: underline; }
.grelha {
  display: grid; gap: 18px; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  border-top: 1px solid var(--linha); padding-top: 18px;
}
.cartao h4 { font-family: Georgia, serif; font-size: 18px; line-height: 1.25; margin: 0 0 6px; }
.vazio { color: var(--suave); }

.rodape { margin-top: 48px; padding-top: 16px; padding-bottom: 32px; border-top: 3px double var(--tinta); font-size: 13px; color: var(--suave); }
.rodape summary { cursor: pointer; }
"""
