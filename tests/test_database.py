import pandas as pd
import pytest

from src.database import carregar_dataframe, salvar_dataframe


def test_persistencia_dataframe_e_indice(tmp_path):
    caminho = tmp_path / "vigia.sqlite3"
    esperado = pd.DataFrame({"ocorrencias": [12, 20]}, index=pd.Index(["IBURA", "COHAB"], name="neighborhood"))

    salvar_dataframe(esperado, "bairros_cluster", caminho)

    pd.testing.assert_frame_equal(carregar_dataframe("bairros_cluster", caminho), esperado)


def test_nome_de_tabela_invalido_rejeitado(tmp_path):
    with pytest.raises(ValueError, match="Nome de tabela inválido"):
        salvar_dataframe(pd.DataFrame({"x": [1]}), "dados; DROP TABLE", tmp_path / "db.sqlite3")
