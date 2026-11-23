# -*- coding: utf-8 -*-
"""Testes do modulo src/relato_cidadao.py."""

import pandas as pd
import pytest

from src.relato_cidadao import (
    registrar_relato,
    consultar_protocolo,
    verificar_relato,
    listar_relatos,
    estatisticas_relatos,
    _salvar_relatos,
    _carregar_relatos,
)


@pytest.fixture(autouse=True)
def _limpar_relatos(tmp_path, monkeypatch):
    """Isola a persistência de cada teste em banco temporário."""
    caminho = tmp_path / "test.sqlite3"
    monkeypatch.setattr("src.relato_cidadao._DATABASE_PATH", caminho)
    if caminho.exists():
        caminho.unlink()


def test_registrar_relato_sucesso():
    relato = registrar_relato(
        descricao="Tiros ouvidos na rua",
        bairro="IBURA",
        tipo_ocorrencia="TIRO",
        data_hora="15/03/2024 21:00",
        anonimo=True,
    )
    assert relato["bairro"] == "IBURA"
    assert relato["tipo_ocorrencia"] == "TIRO"
    assert relato["status"] == "ABERTO"
    assert relato["protocolo"].startswith("VR-")


def test_registrar_relato_descricao_vazia():
    with pytest.raises(ValueError, match="descrição"):
        registrar_relato(descricao="", bairro="IBURA", tipo_ocorrencia="TIRO")


def test_registrar_relato_bairro_vazio():
    with pytest.raises(ValueError, match="bairro"):
        registrar_relato(descricao="Tiros", bairro="", tipo_ocorrencia="TIRO")


def test_consultar_protocolo_encontrado():
    relato = registrar_relato(
        descricao="Teste", bairro="COHAB", tipo_ocorrencia="DISPARO", anonimo=True
    )
    resultado = consultar_protocolo(relato["protocolo"])
    assert resultado is not None
    assert resultado["descricao"] == "Teste"


def test_consultar_protocolo_nao_encontrado():
    resultado = consultar_protocolo("VR-XXXXXX")
    assert resultado is None


def test_verificar_relato_confirmar():
    relato = registrar_relato(
        descricao="Teste", bairro="IBURA", tipo_ocorrencia="AMEACA", anonimo=True
    )
    resultado = verificar_relato(relato["protocolo"], "cidadao1", confirmar=True)
    assert resultado["confirmacoes"] == 1
    assert resultado["status"] == "VERIFICADO"


def test_verificar_relato_confirmar_3x():
    relato = registrar_relato(
        descricao="Teste", bairro="IBURA", tipo_ocorrencia="AMEACA", anonimo=True
    )
    for i in range(3):
        resultado = verificar_relato(relato["protocolo"], f"cidadao{i}", confirmar=True)
    assert resultado["status"] == "CONFIRMADO"


def test_verificar_relato_contestar_3x():
    relato = registrar_relato(
        descricao="Teste", bairro="IBURA", tipo_ocorrencia="AMEACA", anonimo=True
    )
    for i in range(3):
        resultado = verificar_relato(relato["protocolo"], f"cidadao{i}", confirmar=False)
    assert resultado["status"] == "DESCARTADO"


def test_listar_relatos_filtro():
    registrar_relato(descricao="A", bairro="IBURA", tipo_ocorrencia="TIRO", anonimo=True)
    registrar_relato(descricao="B", bairro="COHAB", tipo_ocorrencia="DISPARO", anonimo=True)
    df = listar_relatos(bairro="IBURA")
    assert len(df) == 1


def test_estatisticas_relatos_vazio():
    _salvar_relatos([])
    stats = estatisticas_relatos()
    assert stats["total"] == 0
