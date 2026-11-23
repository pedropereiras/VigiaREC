# Sprint 3 — primeiro agente com LangChain, Ollama e Groq

## Objetivo pedagógico

O Agente de Dados recebe uma pergunta e escolhe uma operação de consulta já autorizada. O LLM interpreta a linguagem e decide qual ferramenta chamar; não conecta diretamente ao banco, não escreve SQL e não calcula os indicadores. Os números vêm das funções Python/SQL da Sprint 2.

## Fluxo de uma pergunta

1. `responder_pergunta` recebe o texto e cria/invoca o agente LangChain.
2. `create_agent` envia a pergunta, o prompt de sistema e os schemas das ferramentas ao modelo.
3. O modelo retorna uma chamada estruturada para, por exemplo, `resumo_ocorrencias` com bairro e período.
4. LangChain valida os argumentos pelo schema Pydantic e executa a ferramenta registrada.
5. A ferramenta chama uma consulta parametrizada em `src/tools/queries.py`; SQLite está em modo somente-leitura.
6. O resultado estruturado volta ao modelo, que formula a resposta. A função Python também devolve as evidências e os nomes das ferramentas executadas.

Este é um único agente com ferramentas especializadas, ainda não o grafo multiagente. LangGraph e o Orquestrador ficam para a Sprint 4.

## Arquivos

- `src/agents/data_agent.py`: criação do agente e seleção do provedor Ollama ou Groq.
- `src/agents/data_tools.py`: schemas Pydantic e wrappers LangChain das cinco ferramentas autorizadas.
- `src/prompts/data_agent.py`: instruções, limites e formato esperado de comportamento.
- `.env.example`: nomes das configurações locais, sem credenciais.
- `tests/test_data_agent.py`: agente conectado a um modelo simulado; não chama a rede nem requer Ollama instalado.

## Opção A: Ollama local

1. Instale Ollama pelo site oficial: <https://ollama.com/download>.
2. No terminal, baixe o modelo de exemplo:

   ```powershell
   ollama pull qwen2.5:3b
   ```

3. Copie `.env.example` para `.env`, mantenha `VIGIA_LLM_PROVIDER=ollama` e ajuste `OLLAMA_MODEL` se escolheu outro modelo.
4. Instale as dependências e rode a pipeline para manter o banco atualizado:

   ```powershell
   python -m pip install -r requirements.txt
   python main.py
   ```

5. Faça uma pergunta pelo Python:

   ```powershell
   python -c "from src.agents.data_agent import responder_pergunta; print(responder_pergunta('Quais são os três bairros com mais ocorrências?'))"
   ```

O modelo é executado localmente; não é necessária chave nem há cobrança por chamada de API. O consumo local de memória/CPU/GPU depende do modelo escolhido. O Ollama precisa estar instalado e seu serviço acessível em `OLLAMA_BASE_URL`.

## Opção B: Groq na nuvem

1. Crie uma chave em <https://console.groq.com/keys>.
2. Copie `.env.example` para `.env`, altere `VIGIA_LLM_PROVIDER=groq` e insira a chave somente em `GROQ_API_KEY` no arquivo `.env` local.
3. Instale as dependências e faça a mesma chamada `responder_pergunta` mostrada acima.

```dotenv
VIGIA_LLM_PROVIDER=groq
GROQ_API_KEY=coloque_a_chave_apenas_no_arquivo_local_env
GROQ_MODEL=openai/gpt-oss-20b
```

Groq recebe a pergunta e os resultados agregados das ferramentas pela rede. O agente não envia SQL, endereço, coordenadas ou registros individuais às ferramentas de linguagem. Mesmo assim, revise as políticas de privacidade aplicáveis antes de usar dados institucionais. O uso da API pode gerar cobrança: a tabela oficial de modelos lista preço e limites por conta, e esses valores podem mudar (<https://console.groq.com/docs/models>). O modelo configurado é um exemplo; confira no console se continua disponível e habilitado para tool calling.

## Configuração

`OLLAMA_BASE_URL` e `OLLAMA_MODEL` configuram a opção local; `GROQ_API_KEY` e `GROQ_MODEL` configuram a opção em nuvem. `VIGIA_LLM_PROVIDER` escolhe apenas um provedor por execução.

`.env` é ignorado pelo Git. Não coloque chaves ou informações privadas em prompts, notebooks versionados ou mensagens de erro.

## Limitações e controles

- O agente tem apenas as ferramentas enumeradas em `data_tools.py`; não há ferramenta de SQL genérico.
- As consultas usam parâmetros SQL, validação de intervalo, granularidade e limite de ranking; a conexão é somente-leitura.
- Respostas numéricas devem ser conferidas contra `evidencias` retornadas por `responder_pergunta`.
- Um LLM pode interpretar mal uma pergunta ou explicar incorretamente um resultado. Esta sprint não implementa memória, LangGraph, monitoramento Langfuse nem avaliação automatizada de qualidade semântica.
- O SQLite local já está carregado com a base real. PostgreSQL segue como decisão de infraestrutura futura, não é uma dependência do agente desta sprint.
