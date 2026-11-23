import sqlite3

from fastapi.testclient import TestClient
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import PrivateAttr

import src.api.main as api_module
from src.api.main import create_app


def _criar_banco(caminho):
    conexao = sqlite3.connect(caminho)
    conexao.execute(
        """CREATE TABLE eventos_tratados (
            id TEXT, data TEXT, neighborhood TEXT, main_reason TEXT,
            police_action INTEGER, hora REAL, hora_estimada INTEGER,
            periodo TEXT, dia_semana TEXT
        )"""
    )
    conexao.execute(
        "INSERT INTO eventos_tratados VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("inc-1", "2025-01-01 12:00:00", "IBURA", "HOMICIDIO", 0, 12, 0, "TARDE", "QUARTA-FEIRA"),
    )
    conexao.commit()
    conexao.close()


class ModeloFakeAPI(BaseChatModel):
    respostas: list[AIMessage]
    _indice: int = PrivateAttr(default=0)

    @property
    def _llm_type(self) -> str:
        return "modelo-fake-api"

    @property
    def _identifying_params(self) -> dict:
        return {}

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        mensagem = self.respostas[self._indice]
        self._indice += 1
        return ChatResult(generations=[ChatGeneration(message=mensagem)])


def _modelo_resumo_ibura():
    return ModeloFakeAPI(
        respostas=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "resumo_ocorrencias",
                        "args": {"bairro": "IBURA"},
                        "id": "api-tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="O recorte contém 1 ocorrência no Ibura."),
        ]
    )


def test_api_health_and_query_with_request_id(tmp_path):
    banco = tmp_path / "api.sqlite3"
    _criar_banco(banco)
    app = create_app(modelo=_modelo_resumo_ibura(), caminho_db=banco, api_key="token-teste")

    with TestClient(app) as cliente:
        health = cliente.get("/health")
        resposta = cliente.post(
            "/v1/query",
            headers={"X-API-Key": "token-teste", "X-Request-ID": "req-teste-1"},
            json={"question": "Quantas ocorrências há no Ibura?"},
        )

    assert health.status_code == 200
    assert health.json() == {"status": "ok", "database": "available"}
    assert resposta.status_code == 200
    assert resposta.headers["X-Request-ID"] == "req-teste-1"
    assert resposta.json()["tools_used"] == ["resumo_ocorrencias"]
    assert resposta.json()["evidence"][0]["resultado"]


def test_api_exige_chave_quando_configurada(tmp_path):
    banco = tmp_path / "api.sqlite3"
    _criar_banco(banco)
    app = create_app(modelo=_modelo_resumo_ibura(), caminho_db=banco, api_key="segredo")

    with TestClient(app) as cliente:
        resposta = cliente.post("/v1/query", json={"question": "Pergunta válida?"})

    assert resposta.status_code == 401
    assert "Credencial" in resposta.json()["detail"]


def test_api_rejeita_pergunta_em_branco(tmp_path):
    banco = tmp_path / "api.sqlite3"
    _criar_banco(banco)
    app = create_app(modelo=_modelo_resumo_ibura(), caminho_db=banco)

    with TestClient(app) as cliente:
        resposta = cliente.post("/v1/query", json={"question": "   "})

    assert resposta.status_code == 422


def test_api_health_indica_banco_ausente(tmp_path):
    app = create_app(modelo=_modelo_resumo_ibura(), caminho_db=tmp_path / "ausente.sqlite3")

    with TestClient(app) as cliente:
        resposta = cliente.get("/health")

    assert resposta.status_code == 503
    assert resposta.json()["database"] == "missing"


def test_interface_web_e_arquivos_de_apresentacao(tmp_path, monkeypatch):
    banco = tmp_path / "api.sqlite3"
    _criar_banco(banco)
    mapa = tmp_path / "mapa.html"
    mapa.write_text("<html><body>mapa seguro de teste</body></html>", encoding="utf-8")
    monkeypatch.setattr(api_module, "MAPA_PATH", mapa)
    app = create_app(modelo=_modelo_resumo_ibura(), caminho_db=banco)

    with TestClient(app) as cliente:
        pagina = cliente.get("/")
        script = cliente.get("/static/app.js")
        mapa_response = cliente.get("/mapa")

    assert pagina.status_code == 200
    assert "Vigia Recife" in pagina.text
    assert "v1/query" in script.text
    assert "mapa seguro de teste" in mapa_response.text
