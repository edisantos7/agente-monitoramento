"""
__main__.py — ponto de entrada. Corre com:  python -m agente

Exemplos:
    python -m agente                  # tenta a internet; o que falhar é lido dos ficheiros locais
    python -m agente --fonte local    # só os ficheiros locais (sem internet)
    python -m agente --fonte api      # só a internet (falha se não houver ligação)
"""

import argparse
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from . import config
from .fontes import ErroFonte, ler_api, ler_ficheiro
from .jornal import gerar_html
from .noticias import ler_feeds, ler_ficheiro_noticias
from .relatorio import gerar_markdown, guardar


def obter_leituras(fonte, ficheiro):
    """Devolve (leituras, descrição da fonte usada)."""
    if fonte in ("auto", "api"):
        try:
            return ler_api(), "API Open-Meteo"
        except ErroFonte as erro:
            if fonte == "api":
                raise
            print(f"Aviso: {erro}\nA usar o ficheiro local em vez da API.", file=sys.stderr)
    return ler_ficheiro(ficheiro), f"ficheiro local ({ficheiro.name})"


def obter_noticias(fonte, ficheiro):
    """Devolve (noticias, descrição da fonte usada, avisos dos feeds que falharam)."""
    if fonte in ("auto", "api"):
        try:
            noticias, avisos = ler_feeds()
            return noticias, "RSS de " + ", ".join(_nomes_das_fontes()), avisos
        except ErroFonte as erro:
            if fonte == "api":
                raise
            print(f"Aviso: {erro}\nA usar o ficheiro local de notícias.", file=sys.stderr)
    return ler_ficheiro_noticias(ficheiro), f"ficheiro local ({ficheiro.name})", []


def _nomes_das_fontes():
    nomes = [fonte for lista in config.FEEDS_NOTICIAS.values() for fonte, _ in lista]
    nomes += [fonte for fonte, _, _ in config.FEEDS_POR_CATEGORIA]
    return list(dict.fromkeys(nomes))  # sem repetidos, pela ordem em que aparecem


def main(argumentos=None):
    parser = argparse.ArgumentParser(prog="agente", description="Agente de monitorização automatizado.")
    parser.add_argument("--fonte", choices=["auto", "api", "local"], default="auto", help="de onde ler os dados")
    parser.add_argument("--ficheiro", type=Path, default=config.FICHEIRO_EXEMPLO, help="JSON da meteorologia local")
    parser.add_argument(
        "--ficheiro-noticias", type=Path, default=config.FICHEIRO_NOTICIAS_EXEMPLO, help="JSON das notícias locais"
    )
    parser.add_argument("--pasta", type=Path, default=config.PASTA_REPORTS, help="onde guardar o relatório")
    parser.add_argument("--sem-abrir", action="store_true", help="não abrir o jornal no browser no fim")
    parser.add_argument(
        "--sem-resumos", action="store_true", help="jornal só com títulos e links (versão para o site público)"
    )
    args = parser.parse_args(argumentos)

    try:
        leituras, descricao = obter_leituras(args.fonte, args.ficheiro)
        noticias, descricao_noticias, avisos = obter_noticias(args.fonte, args.ficheiro_noticias)
    except ErroFonte as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1

    for aviso in avisos:
        print(f"Aviso: feed sem resposta — {aviso}", file=sys.stderr)

    agora = datetime.now()
    dados = dict(agora=agora, noticias=noticias, fonte_noticias=descricao_noticias, avisos=avisos)

    caminho_md = guardar(gerar_markdown(leituras, descricao, **dados), args.pasta, agora)
    html = gerar_html(leituras, descricao, **dados, resumos=not args.sem_resumos)
    caminho_html = guardar(html, args.pasta, agora, "jornal", "html")
    print(f"Relatório guardado em: {caminho_md}")
    print(f"Jornal guardado em:    {caminho_html}")

    if not args.sem_abrir:
        webbrowser.open(caminho_html.as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
