# Sprint 4 — Orquestrador e fluxo LangGraph

## Objetivo

Conectar Orquestrador, Agente de Dados e Agente Analista em um workflow com estado compartilhado, transições condicionais e caminhos de erro. O grafo é explícito e testável; LangGraph controla a execução, não decide os valores das métricas.

## Arquitetura implementada

`src/graph/state.py` define `VigiaState` com os campos `question`, `intent`, `plan`, `filters`, `retrieved_data`, `tools_used`, `analysis`, `final_response` e `errors`.

`src/graph/workflow.py` liga os nós:

```text
START → orquestrador ── pergunta inválida/fora de escopo ──→ finalizar → END
                  └── pergunta analítica ─→ agente_dados
                                              ├── falha/sem ferramenta → finalizar
                                              └── evidências → agente_analista → finalizar → END
```

- **Orquestrador:** valida a pergunta, atribui intenção inicial e plano. A classificação inicial é determinística e pequena; o Agente de Dados faz a seleção semântica da ferramenta.
- **Agente de Dados:** faz uma chamada de tool-calling LangChain e executa apenas ferramentas registradas da Sprint 2. Não faz uma segunda chamada para redigir resposta.
- **Agente Analista:** recebe pergunta, filtros e resultados agregados, e redige uma interpretação limitada às evidências. Não possui ferramentas SQL.
- **Finalização:** entrega resposta e mantém estado, evidências e ferramentas usadas; erros são convertidos em mensagens controladas.

O fluxo usa até **duas chamadas ao modelo** por pergunta suportada: uma para seleção de ferramentas e uma para interpretação. Com Groq, cada chamada pode consumir tokens e gerar cobrança. O limite de recursão da conversa não substitui um limite de requisições do provedor; o grafo limita tool calls a três por pergunta.

## Como executar

```powershell
python -c "from src.graph.workflow import consultar_vigia; resultado=consultar_vigia('Compare as ocorrências de 2024 e 2025'); print(resultado['final_response']); print(resultado['retrieved_data'])"
```

O grafo usa o modelo selecionado em `.env` (`ollama` ou `groq`). As credenciais nunca fazem parte do estado do grafo nem dos prompts.

## Testes

`tests/test_graph_workflow.py` utiliza um modelo simulado para verificar o fluxo de consulta, a passagem de evidências, o caminho de erro sem tool call, a validação de pergunta vazia e o bloqueio de previsão. Nenhuma chamada externa é necessária para a suíte.

## Limitações conhecidas

- O classificador do Orquestrador usa palavras-chave e é apenas uma triagem inicial; não é um classificador semântico robusto.
- Não há persistência de conversas, checkpoint, streaming, FastAPI, Langfuse ou avaliação sistemática das respostas ainda.
- O modelo ainda pode explicar incorretamente uma evidência. A resposta deve ser auditada junto de `retrieved_data`, que contém os resultados determinísticos.
- A seleção de tool calling do Groq depende do modelo continuar habilitado para ferramentas no catálogo do provedor.
