# -*- coding: utf-8 -*-
"""
Exporta sob demanda tabelas SQLite para importacao no Power BI.

Gera versões com encoding UTF-8 BOM e textos limpos em data/exports/powerbi/.

Uso:
    python scripts/preparar_powerbi.py
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import BASE_DIR
from src.database import carregar_dataframe

OUTPUT_DIR = BASE_DIR / "data" / "exports" / "powerbi"


def _limpar_texto(s: pd.Series) -> pd.Series:
    """Remove acentos e padroniza para Power BI."""
    mapa = {
        "Á": "A", "Ã": "A", "Â": "A", "À": "A",
        "É": "E", "Ê": "E",
        "Í": "I",
        "Ó": "O", "Õ": "O", "Ô": "O",
        "Ú": "U",
        "Ç": "C",
        "Ñ": "N",
    }
    resultado = s.copy()
    for antigo, novo in mapa.items():
        resultado = resultado.str.replace(antigo, novo, regex=False)
    return resultado


def preparar_eventos():
    try:
        df = carregar_dataframe("eventos_tratados")
    except ValueError as exc:
        print(exc)
        return None
    print(f"Eventos carregados: {len(df)} registros, {len(df.columns)} colunas")

    colunas_texto = ["neighborhood", "main_reason", "race", "genre", "periodo", "ageGroup", "dia_semana", "nome_mes"]
    for col in colunas_texto:
        if col in df.columns:
            df[col] = _limpar_texto(df[col].astype(str))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "eventos_powerbi.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Salvo: {output_path}")
    return df


def preparar_bairros():
    try:
        df = carregar_dataframe("bairros_cluster")
    except ValueError as exc:
        print(exc)
        return None
    print(f"Bairros carregados: {len(df)} registros")

    if "neighborhood" in df.columns:
        df["neighborhood"] = _limpar_texto(df["neighborhood"].astype(str))

    colunas_texto = [c for c in df.columns if c.startswith("periodo_") or c.startswith("tipo_")]
    for col in colunas_texto:
        df[col] = _limpar_texto(df[col].astype(str))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "bairros_powerbi.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Salvo: {output_path}")
    return df


def preparar_acao_policial():
    try:
        df = carregar_dataframe("acao_policial_por_bairro")
    except ValueError as exc:
        print(exc)
        return None
    print(f"Acao policial carregada: {len(df)} registros")

    if "neighborhood" in df.columns:
        df["neighborhood"] = _limpar_texto(df["neighborhood"].astype(str))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "acao_policial_powerbi.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Salvo: {output_path}")
    return df


def main():
    print("=" * 60)
    print("Preparando dados para Power BI")
    print("=" * 60)

    df_eventos = preparar_eventos()
    df_bairros = preparar_bairros()
    df_acao = preparar_acao_policial()

    print()
    print("=" * 60)
    print("Resumo:")
    if df_eventos is not None:
        print(f"  eventos_powerbi.csv:      {len(df_eventos)} registros x {len(df_eventos.columns)} colunas")
    if df_bairros is not None:
        print(f"  bairros_powerbi.csv:      {len(df_bairros)} registros x {len(df_bairros.columns)} colunas")
    if df_acao is not None:
        print(f"  acao_policial_powerbi.csv: {len(df_acao)} registros x {len(df_acao.columns)} colunas")
    print()
    print(f"Arquivos de intercâmbio salvos em: {OUTPUT_DIR}")
    print("Importe-os no Power BI Desktop > Obter dados > Texto/CSV")


if __name__ == "__main__":
    main()
