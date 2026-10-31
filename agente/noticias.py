"""
noticias.py — recolhe notícias dos feeds RSS e escolhe as principais do dia.

Cada notícia fica neste formato, venha do RSS ou do ficheiro local:

    {"titulo": "...", "link": "https://...", "resumo": "...", "imagem": "https://..." ou None,
     "fonte": "RTP Notícias", "data": datetime com fuso horário}

E o conjunto é um dicionário por secção:  {"nacional": [...], "internacional": [...], ...}

Depois de escolhidas (selecionar_do_dia), cada notícia ganha ainda "tambem_em": a lista
de outros jornais que deram a mesma história — {"fonte": ..., "link": ...}.
"""

import html
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.utils import parsedate_to_datetime
from itertools import groupby
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from . import config
from .fontes import ErroFonte

FUSO = ZoneInfo(config.FUSO_HORARIO)
TAMANHO_RESUMO = 220  # caracteres
MEDIA = "{http://search.yahoo.com/mrss/}"
CONTEUDO = "{http://purl.org/rss/1.0/modules/content/}encoded"

# Imagens genéricas que alguns feeds põem quando a notícia não tem fotografia.
IMAGENS_GENERICAS = ("default_rtpnoticias",)

# Palavras demasiado comuns para dizer se duas notícias falam do mesmo assunto.
PALAVRAS_VAZIAS = set(
    "que com por para dos das nos nas uma uns umas ser mais sem foi sao diz apos sobre entre esta "
    "este isto pelo pela pelos pelas como mas quando onde tem ter vai vao sua seu suas seus ainda "
    "ja nao sim ate desde contra the and".split()
)


def interpretar_rss(xml, fonte, categorias=None):
    """
    Transforma o XML de um feed RSS 2.0 numa lista de notícias.

    Com `categorias` ({"Desporto": "desporto", ...}) cada notícia ganha a chave "secao"
    e as que não tiverem nenhuma dessas categorias são ignoradas.
    """
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError as erro:
        raise ErroFonte(f"Feed de {fonte} com XML inválido: {erro}") from erro

    noticias = []
    itens = list(raiz.iter("item"))
    sem_data = 0
    for item in itens:
        titulo = limpar_html(item.findtext("title", ""))
        link = (item.findtext("link") or "").strip()
        etiquetas = [(c.text or "").strip() for c in item.findall("category")]
        if not titulo or not link or e_opiniao(link, etiquetas):
            continue
        data = ler_data(item.findtext("pubDate", ""))
        if data is None:
            sem_data += 1  # sem data não dá para saber se é de hoje
            continue

        noticia = {
            "titulo": titulo,
            "link": link,
            "resumo": encurtar(limpar_html(item.findtext("description", ""))),
            "imagem": extrair_imagem(item),
            "fonte": fonte,
            "data": data,
        }
        if categorias is not None:
            secao = next((categorias[e] for e in etiquetas if e in categorias), None)
            if secao is None:
                continue
            noticia["secao"] = secao
        noticias.append(noticia)

    if itens and sem_data == len(itens):
        raise ErroFonte(f"Feed de {fonte} com datas num formato desconhecido")
    return noticias


def ler_data(texto):
    """
    Lê a data de publicação. Aceita o formato do RSS ("Sat, 31 Oct 2026 19:52:07 +0000"),
    a variante com "Z" no fim (Record) e o formato ISO sem fuso (Notícias ao Minuto),
    que é tratado como hora de Lisboa. Devolve None se não perceber.
    """
    texto = (texto or "").strip()
    if not texto:
        return None
    try:
        return parsedate_to_datetime(re.sub(r" Z$", " +0000", texto)).astimezone(FUSO)
    except (TypeError, ValueError):
        pass
    try:
        return _no_fuso(datetime.fromisoformat(texto))
    except ValueError:
        return None


def ler_feeds(feeds=config.FEEDS_NOTICIAS, feeds_por_categoria=config.FEEDS_POR_CATEGORIA):
    """Lê todos os feeds em paralelo. Devolve (noticias por secção, avisos dos feeds que falharam)."""
    noticias = {secao: [] for secao in config.SECOES}
    pedidos = [(secao, fonte, url, None) for secao, lista in feeds.items() for fonte, url in lista]
    pedidos += [(None, fonte, url, categorias) for fonte, url, categorias in feeds_por_categoria]

    def ler(pedido):
        secao, fonte, url, categorias = pedido
        resposta = requests.get(url, timeout=config.TIMEOUT_SEGUNDOS, headers={"User-Agent": config.USER_AGENT})
        resposta.raise_for_status()
        return interpretar_rss(resposta.content, fonte, categorias)

    avisos = []
    with ThreadPoolExecutor(max_workers=config.FEEDS_EM_PARALELO) as executor:
        resultados = executor.map(_sem_excecao(ler), pedidos)
        for (secao, fonte, url, _), (lidas, erro) in zip(pedidos, resultados):
            if erro:
                avisos.append(f"{fonte} ({secao or 'várias secções'}): {erro}")
                continue
            for n in lidas:
                noticias.setdefault(n.pop("secao", secao), []).append(n)

    if not any(noticias.values()):
        raise ErroFonte("Nenhum feed de notícias respondeu. " + " | ".join(avisos))
    return noticias, avisos


def ler_ficheiro_noticias(caminho=config.FICHEIRO_NOTICIAS_EXEMPLO):
    """Lê notícias de um ficheiro JSON local (simula os feeds, funciona sem internet)."""
    caminho = Path(caminho)
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        return {
            secao: [
                {"imagem": None, **n, "data": datetime.fromisoformat(n["data"]).astimezone(FUSO)} for n in lista
            ]
            for secao, lista in dados.items()
        }
    except (OSError, ValueError, KeyError, TypeError) as erro:
        raise ErroFonte(f"Falha ao ler {caminho}: {erro}") from erro


def selecionar_do_dia(noticias, agora, secoes=config.SECOES):
    """
    Escolhe as principais notícias de cada secção.

    1. Fica só com as de hoje (hora de Lisboa). Se não houver nenhuma, usa as mais recentes.
    2. Junta a mesma história contada por jornais diferentes numa só notícia.
    3. Ordena pelo número de jornais que a deram (as mais faladas primeiro), depois pela hora,
       alternando entre fontes para não vir tudo do mesmo jornal.

    Devolve {secao: {"itens": [...], "de_hoje": True/False}}, pela ordem de `secoes`.
    """
    hoje = _no_fuso(agora).date()
    resultado = {}
    for secao in [s for s in secoes if s in noticias] + [s for s in noticias if s not in secoes]:
        recentes = sorted(noticias[secao], key=lambda n: n["data"], reverse=True)
        de_hoje = [n for n in recentes if n["data"].date() == hoje]
        grupos = _agrupar_historias(de_hoje or recentes)

        grupos.sort(key=lambda g: (len(g), g[0]["data"]), reverse=True)
        ordenadas = []
        for _, mesmo_tamanho in groupby(grupos, key=len):
            ordenadas += _alternar_fontes(list(mesmo_tamanho))

        maximo = secoes.get(secao, {}).get("maximo", 5)
        resultado[secao] = {
            "itens": [_principal(g) for g in ordenadas[:maximo]],
            "de_hoje": bool(de_hoje),
        }
    return resultado


def limpar_html(texto):
    """Tira etiquetas HTML (ex.: <img> nas descrições da RTP) e espaços a mais."""
    sem_tags = re.sub(r"<[^>]+>", " ", texto or "")
    return " ".join(html.unescape(sem_tags).split())


def encurtar(texto, tamanho=TAMANHO_RESUMO):
    if len(texto) <= tamanho:
        return texto
    return texto[:tamanho].rsplit(" ", 1)[0] + "…"


def extrair_imagem(item):
    """Procura a fotografia da notícia nos sítios onde cada jornal a costuma pôr."""
    candidatos = []
    for etiqueta in ("enclosure", MEDIA + "content", MEDIA + "thumbnail"):
        for e in item.findall(etiqueta):
            tipo = e.get("type", "") + e.get("medium", "")
            if e.get("url") and ("image" in tipo or etiqueta != "enclosure"):
                candidatos.append(e.get("url"))
    for texto in (item.findtext("description", ""), item.findtext(CONTEUDO, "")):
        candidatos += re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', texto or "")

    for url in candidatos:
        url = html.unescape(url)
        if url.startswith("http") and not any(g in url for g in IMAGENS_GENERICAS):
            return url
    return None


def e_opiniao(link, categorias):
    return any(sinal in link or sinal in categorias for sinal in config.SINAIS_OPINIAO)


def palavras_chave(titulo):
    """'Provedoria de Justiça está na manifestação' -> {'provedoria', 'justica', 'manifestacao'}"""
    sem_acentos = unicodedata.normalize("NFKD", titulo.casefold()).encode("ascii", "ignore").decode()
    return {p for p in re.findall(r"[a-z0-9]+", sem_acentos) if len(p) >= 3 and p not in PALAVRAS_VAZIAS}


def mesma_historia(a, b):
    """Duas notícias são a mesma história se os títulos partilham a maior parte das palavras importantes."""
    if a["titulo"].casefold() == b["titulo"].casefold():
        return True
    pa, pb = palavras_chave(a["titulo"]), palavras_chave(b["titulo"])
    comuns = len(pa & pb)
    return comuns >= 3 and comuns / min(len(pa), len(pb)) >= 0.5


def _agrupar_historias(noticias):
    """Junta numa lista cada conjunto de notícias sobre a mesma história (a mais recente primeiro)."""
    grupos = []
    for n in noticias:
        for grupo in grupos:
            if any(mesma_historia(n, outra) for outra in grupo):
                grupo.append(n)
                break
        else:
            grupos.append([n])
    return grupos


def _principal(grupo):
    """A notícia que representa o grupo, com os outros jornais que deram a mesma história."""
    # Preferir uma versão com fotografia para a primeira página.
    principal = next((n for n in grupo if n.get("imagem")), grupo[0])
    outros = {}
    for n in grupo:
        if n["fonte"] != principal["fonte"]:
            outros.setdefault(n["fonte"], n["link"])
    return {**principal, "tambem_em": [{"fonte": f, "link": l} for f, l in outros.items()]}


def _no_fuso(data):
    # Datas sem fuso (ex.: datetime.now()) são tratadas como hora local de Lisboa.
    return data.replace(tzinfo=FUSO) if data.tzinfo is None else data.astimezone(FUSO)


def _alternar_fontes(grupos):
    """[RTP1, RTP2, Púb1, Púb2] -> [RTP1, Púb1, RTP2, Púb2], mantendo a ordem dentro de cada fonte."""
    por_fonte = {}
    for g in grupos:
        por_fonte.setdefault(g[0]["fonte"], []).append(g)
    filas = list(por_fonte.values())
    alternados = []
    while any(filas):
        for fila in filas:
            if fila:
                alternados.append(fila.pop(0))
    return alternados


def _sem_excecao(funcao):
    """Para o ThreadPoolExecutor: devolve (resultado, None) ou (None, erro) em vez de rebentar."""
    def envolvida(*args):
        try:
            return funcao(*args), None
        except (requests.RequestException, ErroFonte) as erro:
            return None, erro
    return envolvida
