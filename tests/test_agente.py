from datetime import datetime

import pytest
import requests

from agente import fontes
from agente.__main__ import main
from agente.analise import avaliar
from agente.fontes import ErroFonte, ler_ficheiro
from agente.relatorio import gerar_markdown, guardar

LEITURA_NORMAL = {"local": "Coimbra", "temperatura": 20.0, "vento": 10.0, "humidade": 60.0, "hora": "x"}


def test_sem_alertas_quando_tudo_normal():
    assert avaliar([LEITURA_NORMAL]) == []


def test_alerta_de_vento_e_calor():
    leitura = {**LEITURA_NORMAL, "temperatura": 38.0, "vento": 60.0}
    mensagens = [a["mensagem"] for a in avaliar([leitura])]
    assert len(mensagens) == 2
    assert mensagens[0].startswith("Calor")
    assert mensagens[1].startswith("Vento forte")


def test_ficheiro_de_exemplo_e_valido():
    leituras = ler_ficheiro()
    assert len(leituras) == 4


def test_ficheiro_com_campos_em_falta(tmp_path):
    ficheiro = tmp_path / "mau.json"
    ficheiro.write_text('[{"local": "X"}]', encoding="utf-8")
    with pytest.raises(ErroFonte, match="sem os campos"):
        ler_ficheiro(ficheiro)


def test_markdown_tem_tabela_e_alertas():
    md = gerar_markdown(ler_ficheiro(), "teste", agora=datetime(2026, 10, 31, 14, 0, 0))
    assert md.startswith("# Relatório de monitorização")
    assert "31/10/2026 14:00:00" in md
    assert "| Figueira da Foz | 18.2 | 54.0 | 82.0 |" in md
    assert "Vento forte" in md


def test_guardar_cria_ficheiro_com_data(tmp_path):
    caminho = guardar("# ok\n", tmp_path / "reports", agora=datetime(2026, 10, 31, 9, 5, 7))
    assert caminho.name == "relatorio_2026-10-31_090507.md"
    assert caminho.read_text(encoding="utf-8") == "# ok\n"


def test_sem_internet_usa_ficheiro_local(tmp_path, monkeypatch, capsys):
    def sem_rede(*args, **kwargs):
        raise requests.ConnectionError("sem rede")

    monkeypatch.setattr(fontes.requests, "get", sem_rede)
    assert main(["--pasta", str(tmp_path), "--sem-abrir"]) == 0
    assert "A usar o ficheiro local" in capsys.readouterr().err
    assert len(list(tmp_path.glob("relatorio_*.md"))) == 1
    assert len(list(tmp_path.glob("jornal_*.html"))) == 1
