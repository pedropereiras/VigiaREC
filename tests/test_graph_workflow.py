import sqlite3

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import PrivateAttr

from src.graph.workflow import consultar_vigia
from src.agents.orchestrator import planejar_execucao


@pytest.fixture
def banco_grafo(tmp_path):
    caminho = tmp_path / "grafo.sqlite3"
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
            ("id-1", "2025-03-01 13:00:00", "IBURA", "HOMICIDIO", 0, 13, 0, "TARDE", "SÁBADO"),
            ("id-1", "2025-03-01 13:00:00", "IBURA", "HOMICIDIO", 0, 13, 0, "TARDE", "SÁBADO"),
            ("id-2", "2025-03-02 14:00:00", "COHAB", "ROUBO", 1, 14, 0, "TARDE", "DOMINGO"),
        ],
    )
    conexao.commit()
    conexao.close()
    return caminho


class ModeloSimuladoGrafo(BaseChatModel):
    respostas: list[AIMessage]
    _indice: int = PrivateAttr(default=0)

    @property
    def _llm_type(self) -> str:
        return "modelo-simulado-grafo"

    @property
    def _identifying_params(self) -> dict:
        return {}

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        mensagem = self.respostas[self._indice]
        self._indice += 1
        return ChatResult(generations=[ChatGeneration(message=mensagem)])


def test_grafo_orquestra_dados_analise_e_resposta(banco_grafo):
    modelo = ModeloSimuladoGrafo(
        respostas=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "resumo_ocorrencias",
                        "args": {"bairro": "IBURA"},
                        "id": "graph-tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="No Ibura há 1 ocorrência distinta em 2 registros."),
        ]
    )

    estado = consultar_vigia(
        "Quantas ocorrências há no Ibura?", modelo=modelo, caminho_db=banco_grafo
    )

    assert estado["intent"] == "consulta_historica"
    assert estado["plan"] == ["agente_dados", "agente_analista"]
    assert estado["tools_used"] == ["resumo_ocorrencias"]
    assert estado["retrieved_data"][0]["resultado"]
    assert estado["analysis"]["evidencias"] == estado["retrieved_data"]
    assert estado["final_response"] == "No Ibura há 1 ocorrência distinta em 2 registros."
    assert estado["errors"] == []


def test_grafo_nao_chama_modelo_para_pergunta_vazia():
    modelo = ModeloSimuladoGrafo(respostas=[])
    estado = consultar_vigia("  ", modelo=modelo)
    assert "pergunta não pode ser vazia" in estado["final_response"]
    assert estado["errors"]


def test_grafo_recusa_resposta_sem_chamada_de_ferramenta(banco_grafo):
    modelo = ModeloSimuladoGrafo(
        respostas=[AIMessage(content="Acho que há muitas ocorrências.")]
    )
    estado = consultar_vigia(
        "Quantas ocorrências há?", modelo=modelo, caminho_db=banco_grafo
    )
    assert estado["tools_used"] == []
    assert not estado["analysis"]
    assert "não selecionou uma ferramenta" in estado["final_response"]


def test_orquestrador_classifica_comparacao_e_bloqueia_previsao():
    assert planejar_execucao("Compare ocorrências de 2024 e 2025")["intent"] == "comparacao_periodos"
    fora_escopo = planejar_execucao("Preveja os crimes do próximo mês")
    assert fora_escopo["intent"] == "fora_de_escopo"
    assert fora_escopo["plan"] == []
    assert fora_escopo["errors"]
