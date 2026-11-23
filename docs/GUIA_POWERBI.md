# Dashboard Power BI — Vigia Recife

Guia passo a passo para criar um dashboard profissional no Power BI.

---

## 1. Preparacao dos dados

### Arquivos para importar

| Tabela | Arquivo | Descricao |
|--------|---------|-----------|
| `Eventos` | `data/exports/powerbi/eventos_powerbi.csv` | Base principal anonimizada, exportada do SQLite |
| `Bairros` | `data/exports/powerbi/bairros_powerbi.csv` | Perfil comportamental + clusters, exportado do SQLite |
| `AcaoPolicial` | `data/exports/powerbi/acao_policial_powerbi.csv` | % de ação policial por bairro, exportado do SQLite |

Gere os arquivos sob demanda depois de executar a pipeline: `python scripts/preparar_powerbi.py`. O banco local canônico é `data/database/vigia_recife.sqlite3`; arquivos CSV de exportação são descartáveis e podem ser recriados.

### Pre-importacao: corrigir encoding

O Power BI pode ter problemas com acentos. Antes de importar, rode:

```bash
python scripts/preparar_powerbi.py
```

Isso gera versões com encoding UTF-8 BOM em `data/exports/powerbi/`:

```
data/exports/powerbi/
  ├── eventos_powerbi.csv
  ├── bairros_powerbi.csv
  └── acao_policial_powerbi.csv
```

---

## 2. Importar dados no Power BI

### Passo 1: Abrir Power BI Desktop

Baixe em: https://powerbi.microsoft.com/pt-br/desktop/

### Passo 2: Obter dados

1. Clique em **Obter dados** > **Texto/CSV**
2. Navegue ate `VigiaRecife/data/exports/powerbi/`
3. Importe `eventos_powerbi.csv`
   - Encoding: **UTF-8**
   - Delimitador: **Virgula**
   - Clique em **Transformar dados** (nao carregar ainda)

### Passo 3: Transformar dados (Power Query)

Na janela do Power Query Editor:

#### Tabela Eventos:
1. Verifique que a coluna `data` esta como tipo **Data/Hora**
   - Clique com botao direito na coluna `data` > **Tipo de Dados** > **Data/Hora**
2. Verifique que `age` e `hora` estao como **Numero Decimal**
3. Verifique que `police_action`, `hora_estimada`, `fim_semana` estao como **Booleano**
4. Feche e aplique

#### Tabela Bairros:
1. Importe `bairros_powerbi.csv`
2. A coluna `cluster` deve ser **Numero Inteiro**

#### Tabela AcaoPolicial:
1. Importe `acao_policial_powerbi.csv`
2. A coluna `pct_acao` deve ser **Numero Decimal**

### Passo 4: Criar relacionamentos

Vá em **Modelo** (visual na lateral esquerda):

| Tabela A | Coluna | Tabela B | Coluna | Cardinalidade |
|----------|--------|----------|--------|---------------|
| Eventos | neighborhood | Bairros | neighborhood | Muitos para Um |
| Eventos | neighborhood | AcaoPolicial | neighborhood | Muitos para Um |

> Nao crie relacao com `data` entre tabelas (nao ha tabela de calendario ainda).

---

## 3. Criar tabela de calendario (DAX)

Na aba **Modelo**, clique em **Nova Tabela** e cole:

```dax
Calendario = 
ADDCOLUMNS(
    CALENDARAUTO(),
    "Ano", YEAR([Date]),
    "Mes", MONTH([Date]),
    "NomeMes", FORMAT([Date], "MMMM"),
    "Trimestre", "T" & QUARTER([Date]),
    "DiaSemana", FORMAT([Date], "dddd"),
    "DiaSemanaNum", WEEKDAY([Date], 2),
    "AnoMes", FORMAT([Date], "YYYY-MM")
)
```

Depois crie o relacionamento:

| Tabela A | Coluna | Tabela B | Coluna |
|----------|--------|----------|--------|
| Calendario | Date | Eventos | data (convertida para Date) |

> No Power Query, crie uma coluna `data_date` = Date.From([data]) na tabela Eventos para fazer o link.

---

## 4. Medidas DAX (copiar e colar)

Crie cada medida em **Nova Medida** no Power BI:

### KPIs Gerais

```dax
Total Ocorrencias = COUNTROWS(Eventos)
```

```dax
Bairros Mapeados = DISTINCTCOUNT(Eventos[neighborhood])
```

```dax
Periodo Minimo = MIN(Eventos[data])
```

```dax
Periodo Maximo = MAX(Eventos[data])
```

```dax
Idade Media = AVERAGE(Eventos[age])
```

### Acao Policial

```dax
Taxa Acao Policial = 
DIVIDE(
    CALCULATE(COUNTROWS(Eventos), Eventos[police_action] = TRUE()),
    COUNTROWS(Eventos),
    0
) * 100
```

```dax
Total Com Acao Policial = 
CALCULATE(COUNTROWS(Eventos), Eventos[police_action] = TRUE())
```

### Por Periodo

```dax
Ocorrencias Noite = 
CALCULATE(COUNTROWS(Eventos), Eventos[periodo] = "NOITE")
```

```dax
Pct Noite = 
DIVIDE([Ocorrencias Noite], [Total Ocorrencias], 0) * 100
```

### Por Tipo

```dax
Top Tipo = 
VAR TopTipo = 
    TOPN(1, ALL(Eventos[main_reason]), CALCULATE(COUNTROWS(Eventos)), DESC)
RETURN
    IF(COUNTROWS(TopTipo) > 0, MAXX(TopTipo, Eventos[main_reason]), "N/D")
```

### Por Genero

```dax
Pct Homem CIS = 
DIVIDE(
    CALCULATE(COUNTROWS(Eventos), Eventos[genre] = "HOMEM CIS"),
    [Total Ocorrencias],
    0
) * 100
```

```dax
Pct Mulher CIS = 
DIVIDE(
    CALCULATE(COUNTROWS(Eventos), Eventos[genre] = "MULHER CIS"),
    [Total Ocorrencias],
    0
) * 100
```

### Por Faixa Etaria

```dax
Ocorrencias Adulto = 
CALCULATE(COUNTROWS(Eventos), Eventos[ageGroup] = "ADULTO")
```

```dax
Ocorrencias Adolescente = 
CALCULATE(COUNTROWS(Eventos), Eventos[ageGroup] = "ADOLESCENTE")
```

```dax
Ocorrencias Crianca = 
CALCULATE(COUNTROWS(Eventos), Eventos[ageGroup] = "CRIANCA")
```

```dax
Ocorrencias Idoso = 
CALCULATE(COUNTROWS(Eventos), Eventos[ageGroup] = "IDOSO")
```

### Tendencia

```dax
Ocorrencias Mes Anterior = 
CALCULATE(
    [Total Ocorrencias],
    DATEADD(Calendario[Date], -1, MONTH)
)
```

```dax
Variacao Mensal = 
VAR Atual = [Total Ocorrencias]
VAR Anterior = [Ocorrencias Mes Anterior]
RETURN
    IF(NOT(ISBLANK(Anterior)) && Anterior <> 0,
        DIVIDE(Atual - Anterior, Anterior, 0) * 100,
        BLANK()
    )
```

---

## 5. Layout do Dashboard (5 paginas)

### Pagina 1: Visao Geral

**Fundo:** Branco com cabecalho vermelho (#B71C1C)

**Topo (faixa de KPIs):**
| Visual | Metrica | Tamanho |
|--------|---------|---------|
| Card | Total Ocorrencias | 1/5 da largura |
| Card | Bairros Mapeados | 1/5 |
| Card | Idade Media | 1/5 |
| Card | Taxa Acao Policial | 1/5 |
| Card | Pct Noite | 1/5 |

**Meio (2 colunas):**
| Lado Esquerdo (60%) | Lado Direito (40%) |
|---------------------|---------------------|
| Grafico de barras: Top 10 Bairros (neighborhood x count) | Grafico de pizza: Por Genero |
| Grafico de linhas: Evolucao Mensal (AnoMes x count) | Grafico de pizza: Por Race |

**Baixo (1 linha):**
| Metrica | Metrica |
|---------|---------|
| Barra: Por Periodo (MADRUGADA, MANHA, TARDE, NOITE) | Barra: Por Tipo de Ocorrencia |

---

### Pagina 2: Analise Geografica

**Mapa principal (ocupa 70% da tela):**
- Visual: **Mapa** (Power BI built-in)
- Latitude: `latitude`
- Longitude: `longitude`
- Legenda: `main_reason` (cores por tipo)
- Tamanho: `COUNT(id)`
- Filtro: bairros com pelo menos 5 ocorrencias

**Lateral direita (30%):**
| Visual | Dados |
|--------|-------|
| Card | Total no mapa |
| Card | Bairros visiveis |
| Tabela | Top 10 Bairros com cor de alerta (por volume) |
| Filtro slider | Faixa de data |

---

### Pagina 3: Perfil Demografico

**Topo (3 cards):**
| Card | Metrica |
|------|---------|
| Idade Media | `Idade Media` |
| Moda de Idade | `TOPN(1, ALL(Eventos[age]), COUNTROWS(Eventos), DESC)` |
| Mediana | `MEDIANX(ALL(Eventos), Eventos[age])` |

**Meio (2 colunas):**
| Lado Esquerdo | Lado Direito |
|---------------|--------------|
| Piramide etaria (barras empilhadas horizontais): ageGroup x genre (filtrar HOMEM CIS e MULHER CIS) | Grafico de barras: Distribuicao por Race (com "NAO IDENTIFICADO" em cinza) |

**Baixo:**
- Grafico de linhas: Idade media por ano (tendencia etaria)

---

### Pagina 4: Acao Policial

**Topo (3 cards):**
| Card | Metrica |
|------|---------|
| Total com Acao | `Total Com Acao Policial` |
| Taxa Geral | `Taxa Acao Policial` |
| Maior % | MAX(AcaoPolicial[pct_acao]) |

**Meio (2 colunas):**
| Lado Esquerdo (55%) | Lado Direito (45%) |
|---------------------|---------------------|
| Grafico de barras horizontais: % Acao Policial por Bairros (ordenado desc) | Grafico de barras: % Acao por Tipo de Ocorrencia |

**Baixo:**
- Mapa com bolhas: bairros com tamanho = ocorrencias, cor = % acao policial (gradiente vermelho/azul)

---

### Pagina 5: Clusters e Risco

**Topo (explicacao):**
- Texto: "Agrupamento comportamental de bairros (KMeans, k escolhido por cotovelo + silhueta)"

**Meio (2 colunas):**
| Lado Esquerdo (50%) | Lado Direito (50%) |
|---------------------|---------------------|
| Scatter plot: `idade_media` (eixo X) x `acao_policial` (eixo Y), cor = cluster, tamanho = ocorrencias | Grafico de barras empilhadas: Composicao por cluster (periodo do dia) |

**Baixo:**
- Tabela detalhada: cluster x ocorrencias x idade media x % acao policial x % fim de semana x tipo predominante

---

## 6. Formatacao Profissional

### Paleta de cores (aplicar em Formatar > Tema)

| Cor | Uso | Hex |
|-----|-----|-----|
| Vermelho primario | Titulos, KPIs criticos | #B71C1C |
| Azul secundario | Graficos, links | #1976D2 |
| Cinza neutro | Texto secundario, bordas | #9E9E9E |
| Verde positivo | Tendencia de queda | #388E3C |
| Laranja alerta | Tendencia de alta | #FF9800 |
| Fundo | Branco | #FFFFFF |
| Fundo cards | Cinza claro | #F5F5F5 |

### Formatacao dos visuais

1. **Titulos:** Fonte Segoe UI Semibold, 14pt, cor #B71C1C
2. **KPIs:** Fonte Segoe UI Bold, 28pt, cor #B71C1C
3. **Labels:** Fonte Segoe UI, 10pt, cor #666666
4. **Bordas dos cards:** 1px solid #E0E0E0, border-radius 8px
5. **Graficos:** Sem gridlines verticais, gridline horizontal cinza claro
6. **Tooltips:** Formato personalizado com 1 casa decimal

### Configuracoes de pagina

- Tamanho: **16:9** (1280x720)
- Fundo: Branco
- Nome das paginas: "Visao Geral", "Mapa", "Demografia", "Acao Policial", "Clusters"

---

## 7. Filtros Interativos

### Filtro global (aplicado em todas as paginas):
- **Ano** (slicer dropdown)
- **Trimestre** (slicer dropdown)
- **Bairro** (slicer list com busca)

### Filtros por pagina:
- **Pagina 2 (Mapa):** Slider de data, filtro de tipo de ocorrencia
- **Pagina 4 (Acao Policial):** Filtro de cluster

### Configuracoes de interacao entre visuais:
- Desative "Editar interacoes" entre cards (nao devem filtrar uns aos outros)
- Mantenha filtros cruzados entre graficos de barras e mapa
- O slicer de ano deve filtrar todas as paginas

---

## 8. Publicar

### Opcao 1: Arquivo .pbix local
1. Salve como `VigiaRecife_Dashboard.pbix`
2. Compartilhe o arquivo .pbix

### Opcao 2: Power BI Service (nuvem)
1. Clique em **Publicar** no ribbon
2. Faca login com conta Microsoft
3. Publique no workspace desejado
4. Configure agendamento de atualizacao (se dados mudarem)

### Opcao 3: Exportar como PDF/PPT
1. **Arquivo** > **Exportar** > **Exportar para PowerPoint**
2. Ou **Arquivo** > **Imprimir** > **Salvar como PDF**

---

## 9. Comandos Uteis no Power Query

Se precisar ajustar algo no Power Query, aqui van os M codes uteis:

### Renomear colunas com acento
```powerquery
= Table.RenameColumns(Original, {
    {"periodo_MANHÃ", "periodo_MANHA"},
    {"periodo_SÁBADO", "periodo_SABADO"}
})
```

### Converter data
```powerquery
= Table.TransformColumnTypes(Original, {{"data", type datetime}})
```

### Filtrar nulos
```powerquery
= Table.SelectRows(Original, each [age] <> null and [age] <> "")
```

### Criar coluna de faixa etaria (se nao existir)
```powerquery
= Table.AddColumn(Original, "faixa_etaria", each 
    if [age] <= 12 then "CRIANCA"
    else if [age] <= 17 then "ADOLESCENTE"
    else if [age] <= 59 then "ADULTO"
    else "IDOSO"
)
```
