"""
fontes.py — de onde vêm os dados.

As duas fontes devolvem exatamente o mesmo formato (uma lista de "leituras"),
por isso o resto do programa não precisa de saber de onde vieram:

    {"local": "Lisboa", "temperatura": 21.4, "vento": 12.0,
     "humidade": 60.0, "hora": "2026-10-31T14:00"}
"""

import json
from pathlib import Path

import requests

from . import config


class ErroFonte(Exception):
    """Não foi possível obter os dados (sem internet, API em baixo, ficheiro inválido...)."""


def ler_api(locais=config.LOCAIS):
    """Pede à Open-Meteo o tempo atual de cada local."""
    leituras = []
    for local in locais:
        parametros = {
            "latitude": local["latitude"],
            "longitude": local["longitude"],
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "timezone": "Europe/Lisbon",
        }
        try:
            resposta = requests.get(config.URL_API, params=parametros, timeout=config.TIMEOUT_SEGUNDOS)
            resposta.raise_for_status()
            atual = resposta.json()["current"]
        except (requests.RequestException, KeyError, ValueError) as erro:
            raise ErroFonte(f"Falha ao ler a API para {local['nome']}: {erro}") from erro

        leituras.append(
            {
                "local": local["nome"],
                "temperatura": atual["temperature_2m"],
                "vento": atual["wind_speed_10m"],
                "humidade": atual["relative_humidity_2m"],
                "hora": atual["time"],
            }
        )
    return leituras


def ler_ficheiro(caminho=config.FICHEIRO_EXEMPLO):
    """Lê leituras de um ficheiro JSON local (simula a API, funciona sem internet)."""
    caminho = Path(caminho)
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as erro:
        raise ErroFonte(f"Falha ao ler {caminho}: {erro}") from erro

    campos = {"local", "temperatura", "vento", "humidade", "hora"}
    for i, leitura in enumerate(dados):
        em_falta = campos - leitura.keys()
        if em_falta:
            raise ErroFonte(f"Leitura {i} em {caminho.name} sem os campos: {', '.join(sorted(em_falta))}")
    return dados
