# Sprint 5 — API, telemetria e observabilidade

## API FastAPI

`src/api/main.py` publica o grafo da Sprint 4 em:

- `GET /health`: verifica se o SQLite existe e contém `eventos_tratados`.
- `POST /v1/query`: recebe `{ "question": "..." }` e retorna status, resposta, intenção, filtros, ferramentas, evidências, erros e duração.
- `GET /docs`: documentação OpenAPI interativa do FastAPI.

Execução local, a partir de `VigiaRecife/`:

```powershell
python -m pip install -r requirements.txt
python main.py
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Exemplo em PowerShell:

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/v1/query `
  -ContentType 'application/json' `
  -Body '{"question":"Quais são os três bairros com mais ocorrências?"}'
```

Por padrão, o servidor é local. Se `VIGIA_API_KEY` estiver configurada, cada chamada a `/v1/query` exige `X-API-Key`. Não exponha o serviço publicamente sem autenticação, TLS, política de acesso, limitação de taxa e revisão de privacidade.

## Logs e telemetria

- Cada requisição recebe `X-Request-ID`, aceitando um ID externo apenas se estiver em formato seguro.
- Logs comuns registram ID, rota, método, código HTTP e duração; não registram pergunta, resposta, filtros, evidências ou chaves.
- O endpoint retorna `duration_ms`, estado de execução e evidências usadas.
- Consultas síncronas ao grafo são executadas no thread pool para não bloquear o event loop do FastAPI.
- A chave da API opcional é comparada em tempo constante e nunca é devolvida ao cliente.

## Langfuse opcional

Tracing só é ativado quando ambas as variáveis estão configuradas:

```dotenv
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=https://cloud.langfuse.com
```

Sem configuração completa, a API funciona e o tracing fica desligado. Ao habilitar Langfuse, prompts, respostas e chamadas de ferramentas podem ser enviados ao serviço de observabilidade; revise retenção, acesso, política institucional e termos de tratamento dos dados antes de ativar com informação real.

## Códigos de resposta

- `200`: consulta concluída.
- `401`: `X-API-Key` ausente ou incorreta quando autenticação está configurada.
- `422`: requisição inválida ou consulta fora de escopo.
- `502`: erro na recuperação/interpretação do workflow.
- `503`: banco ou agente não pronto.

Falhas inesperadas retornam mensagem genérica ao cliente e são registradas no servidor com `request_id`, sem incluir o texto da pergunta.
