"""Testes da geração do resumo em Markdown (agente.relatorio.gerar_markdown)."""

from datetime import datetime

from agente.relatorio import gerar_markdown

AGORA = datetime(2026, 10, 31, 12, 30, 0)

LEITURAS = [
    {"local": "Figueira da Foz", "temperatura": 15.0, "vento": 10.0, "humidade": 80.0, "hora": "2026-10-31T12:30"},
    {"local": "Lisboa", "temperatura": 21.0, "vento": 60.0, "humidade": 50.0, "hora": "2026-10-31T12:30"},
]


def test_resumo_tem_cabecalho_e_estatisticas():
    md = gerar_markdown(LEITURAS, "teste", agora=AGORA)

    assert md.startswith("# Relatório de monitorização")
    assert "- **Gerado em:** 31/10/2026 12:30:00" in md
    assert "- **Meteorologia:** 2 locais, alertas: 1 — fonte: teste" in md
    assert "Temperatura média: **18.0 °C**" in md
    assert "Mais quente: **Lisboa** (21.0 °C)" in md
    assert "Mais frio: **Figueira da Foz** (15.0 °C)" in md


def test_resumo_mostra_alerta_de_vento():
    md = gerar_markdown(LEITURAS, "teste", agora=AGORA)

    assert "alertas: 1" in md
    assert "⚠️ **Lisboa** — Vento forte: 60.0 km/h" in md


def test_resumo_sem_leituras():
    md = gerar_markdown([], "teste", agora=AGORA)

    assert "Sem leituras para resumir." in md
    assert "✅ Nenhum valor fora dos limites." in md
