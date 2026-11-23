import sqlite3
import sys
import types

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import PrivateAttr

from src.agents.data_agent import _criar_modelo, responder_pergunta
from src.agents.data_tools import criar_ferramentas_dados


@pytest.fixture
def banco_agente(tmp_path):
    caminho = tmp_path / "agente.sqlite3"
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


class ModeloSimulado(BaseChatModel):
    respostas: list[AIMessage]
    _indice: int = PrivateAttr(default=0)

    @property
    def _llm_type(self) -> str:
        return "modelo-simulado-para-testes"

    @property
    def _identifying_params(self) -> dict:
        return {}

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        mensagem = self.respostas[self._indice]
        self._indice += 1
        return ChatResult(generations=[ChatGeneration(message=mensagem)])


def test_ferramentas_expostas_sao_as_autorizadas(banco_agente):
    ferramentas = criar_ferramentas_dados(banco_agente)
    assert {f.name for f in ferramentas} == {
        "resumo_ocorrencias",
        "ranking_bairros",
        "distribuicao_categorias",
        "distribuicao_temporal",
        "comparar_periodos",
    }


def test_agente_chama_ferramenta_e_retorna_evidencia(banco_agente):
    modelo = ModeloSimulado(
        respostas=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "resumo_ocorrencias",
                        "args": {"bairro": "IBURA"},
                        "id": "chamada-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="No recorte consultado há 1 ocorrência distinta no Ibura."),
        ]
    )

    resultado = responder_pergunta(
        "Quantas ocorrências há no Ibura?",
        modelo=modelo,
        caminho_db=banco_agente,
    )

    assert resultado["ferramentas_utilizadas"] == ["resumo_ocorrencias"]
    assert resultado["evidencias"][0]["ocorrencias"] == 1
    assert "1 ocorrência" in resultado["resposta"]


def test_agente_rejeita_pergunta_vazia():
    with pytest.raises(ValueError, match="não pode ser vazia"):
        responder_pergunta("   ", modelo=ModeloSimulado(respostas=[]))


def test_groq_exige_chave_de_api(monkeypatch):
    monkeypatch.setenv("VIGIA_LLM_PROVIDER", "groq")
    # Empty string blocks load_dotenv from picking up the developer's real .env.
    monkeypatch.setenv("GROQ_API_KEY", "")
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        _criar_modelo()


def test_groq_recebe_modelo_e_chave_da_configuracao(monkeypatch):
    configuracao = {}
    modulo_falso = types.ModuleType("langchain_groq")

    def chat_groq_falso(**kwargs):
        configuracao.update(kwargs)
        return object()

    modulo_falso.ChatGroq = chat_groq_falso
    monkeypatch.setitem(sys.modules, "langchain_groq", modulo_falso)
    monkeypatch.setenv("VIGIA_LLM_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "chave-apenas-ficticia-para-teste")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")

    _criar_modelo()

    assert configuracao == {"model": "openai/gpt-oss-20b", "temperature": 0}


def test_provedor_nao_suportado_e_rejeitado(monkeypatch):
    monkeypatch.setenv("VIGIA_LLM_PROVIDER", "provedor-invalido")
    with pytest.raises(ValueError, match="não suportado"):
        _criar_modelo()
