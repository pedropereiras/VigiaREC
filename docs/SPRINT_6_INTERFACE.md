# Sprint 6 — interface e apresentação

## Objetivo

Disponibilizar uma interface web local para consultar o Agente de Dados, inspecionar evidências agregadas e abrir o mapa produzido pela pipeline. A interface é um cliente HTTP da API FastAPI; não acessa SQLite nem incorpora regras analíticas no navegador.

## Componentes

- `src/api/static/index.html`: estrutura acessível da página, exemplos de perguntas e navegação.
- `src/api/static/styles.css`: layout responsivo, cartões de indicadores e barras CSS.
- `src/api/static/app.js`: chamadas HTTP same-origin, apresentação segura com `textContent`, gráficos simples e interação com mapa.
- `src/api/main.py`: serve UI, JavaScript, mapa Folium, relatório, painel e API.

## Fluxo da tela

1. A página chama `GET /health` para exibir a disponibilidade da API e do banco.
2. A pessoa envia uma pergunta para `POST /v1/query`.
3. A resposta mostra interpretação, ferramentas utilizadas, filtros/evidências, KPIs e uma barra de comparação quando a evidência contém uma série.
4. A aba Mapa incorpora `GET /mapa`. Relatório e painel permanecem links para abrir em outra aba.

Os nomes de bairros, categorias e mensagens são inseridos no DOM como texto, não como HTML. A chave opcional `X-API-Key` é digitada em campo de senha e mantida somente na memória da página; não é guardada em `localStorage`.

## Execução local

Na pasta `VigiaRecife/`, atualize os dados e inicie o serviço:

```powershell
python main.py
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

Abra <http://127.0.0.1:8000>. O mapa e os artefatos de apresentação precisam ter sido gerados pela pipeline. A aplicação é vinculada a localhost por padrão; autenticação de API não substitui TLS, autorização por usuário, limitação de taxa ou hardening para publicação externa.

## Gráficos e mapa

Os KPIs e barras são construídos a partir dos resultados estruturados retornados pelo Agente, contando IDs distintos conforme a Sprint 2. O mapa é um artefato Folium preexistente (`outputs/figures/mapa_interativo.html`), não um mapa recalculado no navegador. Os tiles do mapa podem depender de acesso à internet.

## Limites

- A UI é um cliente fino: sem login de usuário, persistência de sessões, chat multi-turn, filtros avançados em formulário ou exportação de relatórios personalizados.
- A interpretação continua limitada pela qualidade/cobertura da base e não representa risco individual.
- A API e a UI não foram preparadas para exposição pública sem controles adicionais de segurança e operação.
