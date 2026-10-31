"""Testes da recolha de notícias (agente.noticias), do relatório e do jornal em HTML."""

from datetime import datetime

import pytest

from agente.fontes import ErroFonte
from agente.jornal import gerar_html
from agente.noticias import (
    FUSO,
    interpretar_rss,
    ler_data,
    ler_ficheiro_noticias,
    mesma_historia,
    selecionar_do_dia,
)
from agente.relatorio import gerar_markdown

AGORA = datetime(2026, 10, 31, 21, 0, 0)
LEITURAS = [{"local": "Lisboa", "temperatura": 20.0, "vento": 10.0, "humidade": 50.0, "hora": "x"}]

# Formato igual ao da RTP: descrição em CDATA com uma <img> lá dentro.
RSS_RTP = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>RTP</title>
  <item>
    <title>Primeira noticia</title>
    <link>https://www.rtp.pt/noticias/pais/a</link>
    <description><![CDATA[ <img src="https://cdn.rtp.pt/foto.jpg?w=350&amp;q=50"/> Resumo &amp; detalhes. ]]></description>
    <pubDate>Sat, 31 Oct 2026 19:52:07 +0000</pubDate>
  </item>
  <item>
    <title>Sem data</title>
    <link>https://www.rtp.pt/noticias/pais/b</link>
  </item>
  <item>
    <title>Foto generica</title>
    <link>https://www.rtp.pt/noticias/pais/c</link>
    <description><![CDATA[ <img src="https://cdn.rtp.pt/default_rtpnoticias.png"/> Texto ]]></description>
    <pubDate>Sat, 31 Oct 2026 18:00:00 +0000</pubDate>
  </item>
  <item>
    <title>Uma cronica</title>
    <link>https://www.publico.pt/2026/10/31/mundo/cronica/x</link>
    <pubDate>Sat, 31 Oct 2026 18:00:00 +0000</pubDate>
  </item>
</channel></rss>"""

# Formato do Observador: um só feed, imagem em media:content, secção pela categoria.
RSS_OBSERVADOR = b"""<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel>
  <item>
    <title>Golo no ultimo minuto</title><link>https://observador.pt/1</link>
    <category>Futebol</category><category>Desporto</category>
    <media:content url="https://observador.pt/foto.jpg" medium="image"/>
    <pubDate>Sat, 31 Oct 2026 19:00:00 +0000</pubDate>
  </item>
  <item>
    <title>Receitas de outono</title><link>https://observador.pt/2</link>
    <category>Lifestyle</category>
    <pubDate>Sat, 31 Oct 2026 19:00:00 +0000</pubDate>
  </item>
</channel></rss>"""


def noticia(titulo, fonte, iso, imagem=None):
    return {"titulo": titulo, "link": f"https://{fonte}/{titulo}", "resumo": "", "fonte": fonte,
            "imagem": imagem, "data": datetime.fromisoformat(iso).astimezone(FUSO)}


def test_interpretar_rss_limpa_html_imagens_e_opiniao():
    noticias = interpretar_rss(RSS_RTP, "RTP Notícias")

    assert [n["titulo"] for n in noticias] == ["Primeira noticia", "Foto generica"]  # sem data e crónica ficam de fora
    assert noticias[0]["resumo"] == "Resumo & detalhes."
    assert noticias[0]["imagem"] == "https://cdn.rtp.pt/foto.jpg?w=350&q=50"
    assert noticias[1]["imagem"] is None  # a imagem genérica da RTP não conta
    assert noticias[0]["data"].tzinfo is not None


def test_feed_por_categoria_escolhe_a_secao():
    noticias = interpretar_rss(RSS_OBSERVADOR, "Observador", {"Desporto": "desporto", "Futebol": "desporto"})

    assert len(noticias) == 1  # "Lifestyle" não está no mapa
    assert noticias[0]["secao"] == "desporto"
    assert noticias[0]["imagem"] == "https://observador.pt/foto.jpg"


@pytest.mark.parametrize("texto, esperado", [
    ("Sat, 31 Oct 2026 19:52:07 +0000", "2026-10-31 19:52"),  # RSS normal (Lisboa = UTC em novembro)
    ("Sat, 31 Oct 2026 20:07:19 Z", "2026-10-31 20:07"),      # Record
    ("2026-10-31 20:05:38", "2026-10-31 20:05"),              # Notícias ao Minuto (sem fuso)
])
def test_ler_data_em_varios_formatos(texto, esperado):
    assert f"{ler_data(texto):%Y-%m-%d %H:%M}" == esperado


def test_feed_com_datas_desconhecidas_da_erro():
    xml = b"<rss><channel><item><title>X</title><link>https://x</link><pubDate>ontem</pubDate></item></channel></rss>"
    with pytest.raises(ErroFonte, match="datas num formato desconhecido"):
        interpretar_rss(xml, "Teste")


def test_interpretar_rss_invalido():
    with pytest.raises(ErroFonte, match="XML inválido"):
        interpretar_rss(b"<rss><channel>", "RTP")


def test_mesma_historia_em_jornais_diferentes():
    rtp = noticia("Provedoria de Justiça está na manifestação de Lisboa a monitorizar PSP", "RTP", "2026-10-31T19:52:00+00:00")
    publico = noticia("Provedoria de Justiça está na manifestação e acampada a monitorizar actuação da PSP",
                      "Público", "2026-10-31T17:23:00+00:00")
    outra = noticia("Proteção Civil da Madeira alerta para chuva forte", "RTP", "2026-10-31T15:50:00+00:00")

    assert mesma_historia(rtp, publico)
    assert not mesma_historia(rtp, outra)


def test_mais_falada_primeiro_e_depois_alterna_fontes():
    noticias = {"nacional": [
        noticia("A", "RTP", "2026-10-31T20:00:00+00:00"),
        noticia("B", "RTP", "2026-10-31T19:00:00+00:00"),
        noticia("C", "Público", "2026-10-31T18:00:00+00:00", imagem="https://foto"),
        noticia("D", "RTP", "2026-10-31T16:00:00+00:00"),
        noticia("c", "Observador", "2026-10-31T17:00:00+00:00"),  # mesma história que C
        noticia("Ontem", "RTP", "2026-10-30T12:00:00+00:00"),
    ]}

    escolha = selecionar_do_dia(noticias, AGORA)["nacional"]

    assert escolha["de_hoje"] is True
    assert [n["titulo"] for n in escolha["itens"]] == ["C", "A", "B", "D"]
    assert escolha["itens"][0]["tambem_em"] == [{"fonte": "Observador", "link": "https://Observador/c"}]


def test_sem_noticias_de_hoje_mostra_as_mais_recentes():
    noticias = {"internacional": [noticia("Antiga", "RTP", "2026-10-29T12:00:00+00:00")]}

    escolha = selecionar_do_dia(noticias, AGORA)["internacional"]

    assert escolha["de_hoje"] is False
    assert escolha["itens"][0]["titulo"] == "Antiga"


def test_relatorio_destaca_manchetes_nacional_e_internacional():
    md = gerar_markdown(LEITURAS, "teste", agora=AGORA, noticias=ler_ficheiro_noticias(), fonte_noticias="teste")

    nacional = md.index("### 🇵🇹 Portugal")
    mundo = md.index("### 🌍 Mundo")
    meteo = md.index("## 🌤️ Meteorologia")
    assert md.index("## 📰 Destaques do dia") < nacional < mundo < meteo

    assert "> **MANCHETE — [\\[EXEMPLO\\] Câmara da Figueira da Foz" in md[nacional:mundo]
    assert "> **MANCHETE — [\\[EXEMPLO\\] Cimeira europeia" in md[mundo:meteo]
    assert "Notícia de ontem" not in md
    assert "- **Notícias:** 3 nacional, 2 internacional — fonte: teste" in md


def test_jornal_html_tem_secoes_manchetes_e_escapa_texto():
    noticias = {
        "nacional": [noticia("Título <com> & símbolos", "RTP", "2026-10-31T20:00:00+00:00", imagem="https://foto.jpg")],
        "desporto": [],
    }

    pagina = gerar_html(LEITURAS, "teste", agora=AGORA, noticias=noticias, fonte_noticias="teste")

    assert pagina.startswith("<!doctype html>")
    assert "Sábado, 31 de outubro de 2026" in pagina
    assert '<section class="secao" id="nacional">' in pagina
    assert '<span class="etiqueta">Manchete</span>' in pagina
    assert "Título &lt;com&gt; &amp; símbolos" in pagina
    assert '<img src="https://foto.jpg"' in pagina
    assert "Sem notícias disponíveis." in pagina  # desporto vazio
    assert "Lisboa" in pagina and "20°" in pagina


def test_jornal_sem_resumos_para_o_site_publico():
    noticias = {"nacional": [{**noticia("Título", "RTP", "2026-10-31T20:00:00+00:00"), "resumo": "Texto do jornal"}]}

    com = gerar_html(LEITURAS, "teste", agora=AGORA, noticias=noticias)
    sem = gerar_html(LEITURAS, "teste", agora=AGORA, noticias=noticias, resumos=False)

    assert "Texto do jornal" in com
    assert "Texto do jornal" not in sem
    assert "Título" in sem
