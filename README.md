# Vigia Recife

**Plataforma de Inteligência Urbana para Análise da Violência no Recife**

O Vigia Recife transforma dados públicos de segurança em informação estratégica
e acionável, conectando cidadãos, gestão pública e policiamento em um mesmo
ecossistema de dados. O objetivo é apoiar a tomada de decisão em segurança
pública com evidência, não com percepção.

---

## Estrutura do repositório

```
VigiaRecife/
├── main.py                  # ponto único de entrada — roda a pipeline completa
├── requirements.txt
├── LICENSE
│
├── src/                     # código-fonte modular (fonte da verdade da lógica)
│   ├── agents/                 # Agente de Dados LangChain
│   │   ├── orchestrator.py      # planejamento inicial e controle de escopo
│   │   └── analyst_agent.py     # interpretação das evidências
│   │   ├── data_agent.py        # recuperação LangChain com tool calling
│   │   └── data_tools.py        # schemas das ferramentas para o LLM
│   ├── prompts/                # instruções versionadas do agente
│   ├── graph/                  # estado e workflow LangGraph
│   ├── api/                    # API HTTP FastAPI
│   │   └── static/             # interface web sem dependência de frontend
│   ├── config.py              # caminhos, paleta de cores, constantes de domínio
│   ├── coleta.py               # leitura da base bruta
│   ├── limpeza.py               # padronização de texto, duplicatas, coordenadas
│   ├── tratamento.py            # datas, idades, artefato de horário (21h)
│   ├── features.py              # engenharia de atributos temporais
│   ├── estatisticas.py          # estatística descritiva
│   ├── graficos.py              # todas as visualizações, incl. pirâmide etária
│   ├── clusterizacao.py         # correlação + clusterização comportamental (KMeans)
│   ├── series_temporais.py      # série mensal, média móvel, teste de tendência
│   ├── acao_policial.py         # indicadores de resposta policial
│   ├── relatorio.py             # consolidação do relatório de saída
│   ├── integracao_externa.py    # integração com SDS-PE (CVLI) e CTTU (trânsito)
│   ├── mapa_interativo.py       # mapa Folium interativo com curva de risco por hora
│   ├── relato_cidadao.py        # relato cidadão com verificação comunitária
│   ├── painel_gestao.py         # painel HTML para prefeitura com triagem automática
│   ├── protocolo_acompanhamento.py  # protocolo público de acompanhamento de relatos
│   └── tools/                    # consultas SQL seguras e análises determinísticas
│
├── notebooks/
│   └── VigiaRecife.ipynb    # notebook narrativo — importa de src/, não redefine lógica
│
├── data/                    # dados locais, ignorados pelo Git
│   ├── csv - eventos.csv      # entrada completa prioritária (5.889 registros)
│   ├── raw/                   # entrada alternativa e base sintética
│   └── database/              # SQLite local com resultados e relatos
│
├── outputs/
│   ├── figures/                # todos os .png gerados + mapa_interativo.html
│   ├── painel_gestao.html      # painel de gestão da prefeitura
│   └── relatorio.txt
│
├── docs/
│   ├── metodologia.md          # decisões metodológicas documentadas e justificadas
│   ├── SPRINT_2_FERRAMENTAS.md  # ferramentas de consulta e análise sem LLM
│   ├── SPRINT_3_AGENTE_DADOS.md # Agente de Dados com Ollama local ou Groq
│   ├── SPRINT_4_LANGGRAPH.md    # orquestração dos agentes
│   ├── SPRINT_5_API_OBSERVABILIDADE.md # API, telemetria e Langfuse
│   ├── SPRINT_6_INTERFACE.md    # interface de consulta e mapa
│   ├── Vigia_Recife_Documentacao_Tecnica.docx
│   └── Vigia_Recife_Relatorio_Projeto.pdf
│
└── tests/
    ├── test_limpeza.py
    ├── test_tratamento.py
    └── test_series_temporais.py
```

**Regra de ouro do projeto:** toda lógica de negócio mora em `src/`. O notebook,
o `main.py` e os testes apenas *chamam* essas funções — nunca redefinem a
mesma lógica em mais de um lugar.

## Como executar

```bash

cd "C:\Users\pedro\OneDrive\Desktop\Vigia-Recife\VigiaRecife"
.\.venv\Scripts\python -m pytest tests/ -q

cd "C:\Users\pedro\OneDrive\Desktop\Vigia-Recife\VigiaRecife"
.\.venv\Scripts\activate.ps1
python main.py

cd "C:\Users\pedro\OneDrive\Desktop\Vigia-Recife\VigiaRecife"

C:\Users\pedro\AppData\Local\Programs\Python\Python312\python.exe -m venv .venv

.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
python scripts\gerar_dados_exemplo.py
$env:VIGIA_CSV_EVENTOS = "data/raw/eventos.csv"
python main.py

dir outputs
dir outputs\figures
start outputs\figures\top_bairros.png
start outputs\figures\serie_mensal.png
start outputs\figures\acao_por_tipo.png
outputs\figures\mapa_interativo.html
start outputs\figures\mapa_interativo.html
ii outputs\figures\mapa_interativo.html
outputs\painel_gestao.html
start outputs\painel_gestao.html
ii outputs\painel_gestao.html
ii outputs
ii outputs\figures
code outputs\figures


python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# por padrão, usa data/csv - eventos.csv quando presente; caso contrário,
# procura data/raw/eventos.csv e data/eventos.csv. Para forçar um caminho:
$env:VIGIA_CSV_EVENTOS = "data/raw/eventos.csv"
python main.py
```

Isso gera tabelas no SQLite local e artefatos em `outputs/` — gráficos, mapa,
painel HTML e relatório de texto.

Para rodar os testes automatizados:

```bash
pytest tests/ -v
```

O desenho, a semântica das contagens e exemplos de uso das ferramentas da Sprint 2 estão em `docs/SPRINT_2_FERRAMENTAS.md`.

## Sprint 3 — Agente de Dados

O agente LangChain chama somente as ferramentas determinísticas da Sprint 2. Pode usar Ollama local ou Groq; escolha um em `.env` (exemplo em `.env.example`).

**Ollama local — sem chave e sem custo por chamada de API:** instale Ollama em <https://ollama.com/download>, execute `ollama pull qwen2.5:3b` e configure:

```dotenv
VIGIA_LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b
```

**Groq — API em nuvem:** crie uma chave em <https://console.groq.com/keys>, configure-a apenas em `.env` e selecione:

```dotenv
VIGIA_LLM_PROVIDER=groq
GROQ_API_KEY=sua_chave_local
GROQ_MODEL=openai/gpt-oss-20b
```

Groq pode cobrar pelo uso; preços e limites atuais estão em <https://console.groq.com/docs/models>. Nesse modo, a pergunta e os resultados agregados enviados ao modelo saem da máquina. O agente não envia endereços, coordenadas ou linhas individuais.

Após `python -m pip install -r requirements.txt` e `python main.py`, teste uma pergunta:

```powershell
python -c "from src.agents.data_agent import responder_pergunta; print(responder_pergunta('Quais são os três bairros com mais ocorrências?'))"
```

O passo a passo e os limites do agente estão em `docs/SPRINT_3_AGENTE_DADOS.md`.

## Sprint 5 — API e observabilidade

Inicie a API local depois de atualizar o banco e configurar um provedor LLM:

```powershell
uvicorn src.api.main:app --host 127.0.0.1 --port 8000
```

A documentação interativa fica em `http://127.0.0.1:8000/docs`; `GET /health` verifica o SQLite e `POST /v1/query` consulta o grafo. Se `VIGIA_API_KEY` estiver definida no `.env`, envie-a no header `X-API-Key`. Langfuse permanece desativado enquanto `LANGFUSE_PUBLIC_KEY` e `LANGFUSE_SECRET_KEY` não estiverem configuradas. Veja `docs/SPRINT_5_API_OBSERVABILIDADE.md` antes de ativar tracing ou expor a API fora de `localhost`.

## Fonte de dados

O CSV padrão é a exportação completa do **Fogo Cruzado** em
`data/csv - eventos.csv`. A aplicação seleciona esse arquivo primeiro e, se
ausente, tenta `data/raw/eventos.csv` e `data/eventos.csv`. Para escolher outra
fonte explicitamente, configure `VIGIA_CSV_EVENTOS`. A coleta não consulta
diretamente a API; o arquivo precisa ser obtido e colocado localmente.

> Antes de redistribuir dados tratados publicamente, confirme os termos de uso
> junto à equipe do Fogo Cruzado — ver `docs/metodologia.md`, seção 7.

**Bases planejadas para próximas integrações:** estatísticas oficiais da
SDS-PE (CVLI), acidentes de trânsito da CTTU e GeoJSON oficial de bairros do
Recife.

## Metodologia

Todas as decisões de tratamento de dados (artefato de horário, subnotificação
racial, escolha de k na clusterização, teste de tendência, limiares mínimos de
agregação) estão documentadas e justificadas em **[`docs/metodologia.md`](docs/metodologia.md)**.

## Principais achados (base 2018–2026)

- 5.889 registros analisados em 91 bairros do Recife
- Sem tendência estatisticamente significativa de crescimento ou queda no período (p ≈ 0,89)
- Apenas 5–6% das ocorrências têm ação policial registrada, com forte desigualdade entre bairros
- Clusterização comportamental revela perfis distintos de violência entre bairros com volume total semelhante

*(resultados completos em `outputs/relatorio.txt` após execução da pipeline)*

## Roadmap

- [x] Pipeline de dados modular, testada e reproduzível
- [x] EDA, clusterização orientada a dados (cotovelo + silhueta) e teste de tendência
- [x] Integração com dados oficiais da SDS-PE e CTTU
- [x] Mapa interativo por bairro/quadra com curva de risco por horário
- [x] Módulo de relato cidadão com verificação comunitária
- [x] Painel de gestão para a prefeitura com triagem automática de demandas
- [x] Protocolo de acompanhamento público de status de relato

## Considerações éticas

Este projeto lida com dados sensíveis de violência e vitimização. O desenho da
plataforma evita apresentar bairros inteiros como "zonas de perigo" de forma
estática — o foco está em padrões comportamentais, temporais e de resposta
institucional, para reduzir o risco de estigmatização territorial e reforçar
ação de gestão pública em vez de vigilância indiscriminada.

Antes de publicar qualquer dado tratado publicamente, ver as recomendações de
anonimização em `docs/metodologia.md`, seção 7.

## Autoria

Desenvolvido por Pedro Pereira — estudante de Banco de Dados com ênfase em
Data Science e IA (CESAR School, Recife).

## Licença

Código sob licença MIT (ver `LICENSE`). Os dados em `data/` seguem os termos
de uso da fonte original (API do Fogo Cruzado), não desta licença.
