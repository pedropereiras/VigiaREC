import sqlite3

import pytest

from src.tools.analytics import comparar_periodos
from src.tools.queries import (
    FiltrosOcorrencia,
    distribuicao_temporal,
    ranking_bairros,
    resumo_ocorrencias,
)


@pytest.fixture
def banco_ocorrencias(tmp_path):
    caminho = tmp_path / "ocorrencias.sqlite3"
    conexao = sqlite3.connect(caminho)
    conexao.execute(
        """CREATE TABLE eventos_tratados (
            id TEXT, data TEXT, neighborhood TEXT, main_reason TEXT,
            police_action INTEGER, hora REAL, hora_estimada INTEGER,
            periodo TEXT, dia_semana TEXT
        )"""
    )
    conexao.executemany(
        "INSERT INTO eventos_tratados VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            ("inc-1", "2025-01-01 21:00:00", "IBURA", "HOMICIDIO", 0, None, 1, None, "QUARTA-FEIRA"),
            ("inc-1", "2025-01-01 21:00:00", "IBURA", "HOMICIDIO", 0, None, 1, None, "QUARTA-FEIRA"),
            ("inc-2", "2025-01-02 13:00:00", "IBURA", "HOMICIDIO", 1, 13, 0, "TARDE", "QUINTA-FEIRA"),
            ("inc-4", "2025-01-02 15:00:00", "IBURA", "HOMICIDIO", 0, 15, 0, "TARDE", "QUINTA-FEIRA"),
            ("inc-3", "2025-01-03 18:00:00", "COHAB", "ROUBO", 0, 18, 0, "NOITE", "SEXTA-FEIRA"),
        ],
    )
    conexao.commit()
    conexao.close()
    return caminho


def test_resumo_distingue_linhas_de_incidentes(banco_ocorrencias):
    resumo = resumo_ocorrencias(caminho=banco_ocorrencias)
    assert resumo["registros"] == 5
    assert resumo["ocorrencias"] == 4
    assert resumo["bairros"] == 2
    assert resumo["ocorrencias_com_acao"] == 1
    assert resumo["taxa_acao_policial"] == pytest.approx(1 / 4)


def test_filtros_e_ranking_usam_parametros(banco_ocorrencias):
    filtros = FiltrosOcorrencia(bairro=" ibura ", data_inicio="2025-01-01", data_fim="2025-01-02")
    resumo = resumo_ocorrencias(filtros, banco_ocorrencias)
    assert resumo["ocorrencias"] == 3
    ranking = ranking_bairros(5, filtros, banco_ocorrencias)
    assert ranking == [{"bairro": "IBURA", "ocorrencias": 3, "registros": 4}]


def test_filtro_de_injection_nao_altera_consulta(banco_ocorrencias):
    filtros = FiltrosOcorrencia(bairro="IBURA' OR 1=1 --")
    assert resumo_ocorrencias(filtros, banco_ocorrencias)["ocorrencias"] == 0


def test_serie_horaria_omite_horario_estimado(banco_ocorrencias):
    serie = distribuicao_temporal("hora", caminho=banco_ocorrencias)
    assert serie == [
        {"periodo": 13, "ocorrencias": 1, "registros": 1},
        {"periodo": 15, "ocorrencias": 1, "registros": 1},
        {"periodo": 18, "ocorrencias": 1, "registros": 1},
    ]


def test_serie_mensal_agrupa_por_mes_e_nao_por_periodo_do_dia(banco_ocorrencias):
    serie = distribuicao_temporal("mes", caminho=banco_ocorrencias)
    assert serie == [{"periodo": "2025-01", "ocorrencias": 4, "registros": 5}]


def test_validacao_de_datas_e_limite():
    with pytest.raises(ValueError, match="data_inicio"):
        FiltrosOcorrencia(data_inicio="2025-02-01", data_fim="2025-01-01")
    with pytest.raises(ValueError, match="limite"):
        ranking_bairros(101)


def test_comparacao_de_periodos_calcula_variacao(banco_ocorrencias):
    comparacao = comparar_periodos(
        ("2025-01-01", "2025-01-02"),
        ("2025-01-03", "2025-01-03"),
        caminho=banco_ocorrencias,
    )
    assert comparacao["variacao_absoluta"] == -2
    assert comparacao["variacao_percentual"] == pytest.approx(-200 / 3)


def test_comparacao_sem_periodo_base_nao_divide_por_zero(banco_ocorrencias):
    comparacao = comparar_periodos(
        ("2024-01-01", "2024-01-31"),
        ("2025-01-03", "2025-01-03"),
        caminho=banco_ocorrencias,
    )
    assert comparacao["variacao_percentual"] is None
    assert comparacao["variacao_percentual_definida"] is False
