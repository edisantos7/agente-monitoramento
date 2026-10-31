"""
analise.py — compara as leituras com os limites e decide o que é um alerta.
"""

from . import config


def avaliar(leituras, limites=config.LIMITES):
    """Devolve uma lista de alertas: {"local": ..., "mensagem": ...}."""
    alertas = []
    for l in leituras:
        if l["temperatura"] >= limites["temperatura_max"]:
            alertas.append(_alerta(l, f"Calor: {l['temperatura']} °C (limite {limites['temperatura_max']} °C)"))
        if l["temperatura"] <= limites["temperatura_min"]:
            alertas.append(_alerta(l, f"Frio: {l['temperatura']} °C (limite {limites['temperatura_min']} °C)"))
        if l["vento"] >= limites["vento_max"]:
            alertas.append(_alerta(l, f"Vento forte: {l['vento']} km/h (limite {limites['vento_max']} km/h)"))
        if l["humidade"] >= limites["humidade_max"]:
            alertas.append(_alerta(l, f"Humidade alta: {l['humidade']} % (limite {limites['humidade_max']} %)"))
    return alertas


def estatisticas(leituras):
    """Médias, máximos e mínimos de todas as leituras."""
    if not leituras:
        return {}
    temperaturas = [l["temperatura"] for l in leituras]
    ventos = [l["vento"] for l in leituras]
    return {
        "temperatura_media": round(sum(temperaturas) / len(temperaturas), 1),
        "temperatura_max": max(leituras, key=lambda l: l["temperatura"]),
        "temperatura_min": min(leituras, key=lambda l: l["temperatura"]),
        "vento_max": max(ventos),
    }


def _alerta(leitura, mensagem):
    return {"local": leitura["local"], "mensagem": mensagem}
