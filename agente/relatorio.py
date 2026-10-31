"""
relatorio.py — transforma os dados recolhidos num resumo em Markdown e guarda os relatórios em reports/.

Ordem do relatório: cabeçalho, destaques de notícias (uma secção de cada vez), meteorologia.
"""

from datetime import datetime
from pathlib import Path

from . import config
from .analise import avaliar, estatisticas
from .noticias import selecionar_do_dia


def gerar_markdown(leituras, fonte, agora=None, noticias=None, fonte_noticias=None, avisos=()):
    """
    Constrói o texto do relatório. Não escreve nada no disco.

    `noticias` é o dicionário {"nacional": [...], "internacional": [...], ...} de agente.noticias;
    sem ele, o relatório tem só a meteorologia.
    """
    agora = agora or datetime.now()
    alertas = avaliar(leituras)
    destaques = selecionar_do_dia(noticias, agora) if noticias is not None else None

    linhas = [
        "# Relatório de monitorização",
        "",
        f"- **Gerado em:** {agora:%d/%m/%Y %H:%M:%S}",
    ]
    if destaques is not None:
        contagem = ", ".join(f"{len(d['itens'])} {secao}" for secao, d in destaques.items())
        linhas.append(f"- **Notícias:** {contagem} — fonte: {fonte_noticias}")
    linhas += [
        f"- **Meteorologia:** {len(leituras)} locais, alertas: {len(alertas)} — fonte: {fonte}",
        "",
    ]
    if avisos:
        linhas += ["> ⚠️ **Avisos da recolha:**"] + [f"> - {a}" for a in avisos] + [""]

    if destaques is not None:
        linhas += _secao_noticias(destaques)
    linhas += _secao_meteorologia(leituras, alertas)

    return "\n".join(linhas) + "\n"


def guardar(conteudo, pasta=config.PASTA_REPORTS, agora=None, prefixo="relatorio", extensao="md"):
    """Guarda o relatório com a data e hora no nome e devolve o caminho do ficheiro."""
    agora = agora or datetime.now()
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / f"{prefixo}_{agora:%Y-%m-%d_%H%M%S}.{extensao}"
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho


def titulo_secao(secao):
    info = config.SECOES.get(secao, {"titulo": secao.capitalize(), "emoji": "📰"})
    return f"{info['emoji']} {info['titulo']}"


def _secao_noticias(destaques):
    linhas = ["## 📰 Destaques do dia", ""]
    for secao, destaque in destaques.items():
        itens = destaque["itens"]
        linhas += [f"### {titulo_secao(secao)}", ""]

        if not itens:
            linhas += ["Sem notícias disponíveis.", ""]
            continue
        if not destaque["de_hoje"]:
            linhas += ["*Ainda não há notícias de hoje nesta secção — a mostrar as mais recentes.*", ""]

        manchete, *outras = itens
        linhas += [
            f"> **MANCHETE — {_link(manchete)}**",
            ">",
            f"> {manchete['resumo']}" if manchete["resumo"] else ">",
            ">",
            f"> *{_origem(manchete)}*",
            "",
        ]
        if outras:
            linhas += ["**Outras notícias:**", ""]
            linhas += [f"{i}. {_link(n)} — *{_origem(n)}*" for i, n in enumerate(outras, start=2)]
            linhas.append("")
    return linhas


def _secao_meteorologia(leituras, alertas):
    stats = estatisticas(leituras)
    linhas = ["## 🌤️ Meteorologia", "", "### Resumo", ""]

    if stats:
        linhas += [
            f"- Temperatura média: **{stats['temperatura_media']} °C**",
            f"- Mais quente: **{stats['temperatura_max']['local']}** ({stats['temperatura_max']['temperatura']} °C)",
            f"- Mais frio: **{stats['temperatura_min']['local']}** ({stats['temperatura_min']['temperatura']} °C)",
            f"- Vento mais forte: **{stats['vento_max']} km/h**",
        ]
    else:
        linhas.append("Sem leituras para resumir.")

    linhas += ["", "### Alertas", ""]
    if alertas:
        linhas += [f"- ⚠️ **{a['local']}** — {a['mensagem']}" for a in alertas]
    else:
        linhas.append("✅ Nenhum valor fora dos limites.")

    linhas += [
        "",
        "### Leituras",
        "",
        "| Local | Temperatura (°C) | Vento (km/h) | Humidade (%) | Hora da leitura |",
        "|---|---:|---:|---:|---|",
    ]
    linhas += [
        f"| {l['local']} | {l['temperatura']} | {l['vento']} | {l['humidade']} | {l['hora']} |" for l in leituras
    ]
    return linhas


def _link(noticia):
    # Parênteses retos no título partiriam o link em Markdown.
    titulo = noticia["titulo"].replace("[", "\\[").replace("]", "\\]")
    return f"[{titulo}]({noticia['link']})"


def _origem(noticia):
    origem = f"{noticia['fonte']} · {noticia['data']:%H:%M}"
    if noticia.get("tambem_em"):
        origem += " · também em " + ", ".join(f"[{o['fonte']}]({o['link']})" for o in noticia["tambem_em"])
    return origem
