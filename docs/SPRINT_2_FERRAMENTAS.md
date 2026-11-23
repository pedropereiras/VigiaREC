# Sprint 2 — ferramentas determinísticas de dados e análise

## Objetivo

Disponibilizar operações de domínio seguras e testáveis para consulta ao SQLite. Essas funções serão a fronteira que um futuro agente de dados poderá chamar; elas não recebem nem executam SQL gerado por um LLM.

## Módulos

- `src/tools/queries.py`: filtros validados, conexão SQLite somente-leitura e consultas parametrizadas.
- `src/tools/analytics.py`: cálculos determinísticos sobre os resultados das consultas, atualmente comparação de períodos.
- `tests/test_tools_queries.py`: valida a contagem por incidente, filtros, segurança de parâmetros, série horária e variação entre períodos.

## Semântica de contagem

O arquivo-fonte tem 5.889 linhas, mas o campo `id` tem 5.036 valores distintos. As linhas representam registros de pessoas associados a ocorrências; um mesmo incidente pode aparecer em várias linhas. Por isso, as ferramentas expõem os dois conceitos:

- `registros`: quantidade de linhas importadas da fonte;
- `ocorrencias`: quantidade de IDs de incidente distintos (`COUNT(DISTINCT id)`).

Rankings, séries e comparações usam incidentes distintos. Evita-se apresentar linhas importadas como se fossem eventos independentes. O `id` repetido é tratado como identificador do incidente; `id_victim` é distinto em todos os valores preenchidos, mas está ausente em 327 linhas. A semântica de cada linha e a modelagem normalizada incidente–pessoa devem ser confirmadas com a documentação da fonte antes de consolidar o esquema PostgreSQL.

## Ferramentas disponíveis

```python
from src.tools.queries import (
    FiltrosOcorrencia,
    resumo_ocorrencias,
    ranking_bairros,
    distribuicao_categorias,
    distribuicao_temporal,
)
from src.tools.analytics import comparar_periodos

filtros = FiltrosOcorrencia(
    bairro="IBURA",
    data_inicio="2024-01-01",
    data_fim="2024-12-31",
)
resumo = resumo_ocorrencias(filtros)
ranking = ranking_bairros(limite=10)
horas = distribuicao_temporal("hora")
comparacao = comparar_periodos(
    ("2024-01-01", "2024-12-31"),
    ("2025-01-01", "2025-12-31"),
)
```

Datas devem estar no formato ISO (`YYYY-MM-DD`). Os intervalos são inclusivos. A série horária exclui registros marcados como hora estimada e não inventa um horário para eles. Se o período de referência da comparação não tiver ocorrências, a variação percentual retorna `None` e é sinalizada como indefinida.

## Segurança da camada SQL

- A conexão abre o arquivo SQLite em modo `mode=ro` e ativa `PRAGMA query_only`.
- SQL e colunas são definidos no código; valores dos filtros são enviados por parâmetros (`?`).
- Filtros de data, granularidade temporal e limite do ranking são validados antes da consulta.
- As funções públicas expõem operações de negócio, não um executor genérico de SQL.

## Limites e próxima etapa

Esta sprint opera sobre o SQLite local que o projeto já utiliza. Ainda não há servidor PostgreSQL nem configuração de conexão no repositório. Para o MVP local, SQLite mantém o fluxo simples; PostgreSQL poderá substituir o adaptador de persistência quando o serviço multiusuário/API entrar no escopo, preservando as mesmas funções e testes de domínio.

O módulo de análise não usa LLM: contagens, rankings e percentuais são calculados por SQL/Python. Na sprint de agentes, o LLM poderá selecionar a ferramenta apropriada e explicar os resultados estruturados, sem produzir os números.
