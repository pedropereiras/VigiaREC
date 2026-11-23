# -*- coding: utf-8 -*-
"""Migra CSVs/JSONs processados legados para SQLite sem apagar os originais."""

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_PROCESSED_DIR
from src.database import carregar_relatos, salvar_dataframe, salvar_relatos


def main() -> None:
    arquivos = {
        "eventos_tratados.csv": ("eventos_tratados", None),
        "bairros_cluster.csv": ("bairros_cluster", "neighborhood"),
        "acao_policial_por_bairro.csv": ("acao_policial_por_bairro", "neighborhood"),
        "base_integrada.csv": ("base_integrada", None),
    }
    for nome, (tabela, coluna_indice) in arquivos.items():
        origem = DATA_PROCESSED_DIR / nome
        if not origem.exists():
            continue
        dataframe = pd.read_csv(origem, index_col=coluna_indice)
        if coluna_indice:
            dataframe.index.name = coluna_indice
        salvar_dataframe(dataframe, tabela)
        print(f"Migrado {origem.name}: {len(dataframe)} registros -> {tabela}")

    legado_relatos = DATA_PROCESSED_DIR / "relatos.json"
    if legado_relatos.exists():
        relatos_existentes = carregar_relatos()
        if relatos_existentes:
            print("Migração de relatos ignorada: o banco já contém relatos.")
        else:
            with legado_relatos.open(encoding="utf-8") as arquivo:
                relatos = json.load(arquivo)
            salvar_relatos(relatos)
            print(f"Migrados {len(relatos)} relatos de relatos.json.")

    print("Migração concluída; os arquivos de origem foram preservados.")


if __name__ == "__main__":
    main()
