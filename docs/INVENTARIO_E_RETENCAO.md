# Inventário da estrutura e critérios de retenção

## Fronteira do repositório

O repositório está delimitado ao Vigia Recife e à análise de ocorrências de segurança pública no Recife. O acervo GEVACZ de ovitrampas, estações disseminadoras e distritos sanitários foi removido do projeto conforme solicitação do responsável, pois pertence a outro domínio e não tinha integração funcional com esta aplicação.

## Aplicação `VigiaRecife/`

| Caminho/arquivo | Necessidade e decisão |
|---|---|
| `main.py` | Entrada da pipeline e coordenação das etapas; manter fino, sem regra de negócio. |
| `requirements.txt` | Reprodutibilidade de ambiente; manter versões fixadas. SQLite não exige pacote adicional. |
| `src/config.py` | Caminhos e constantes do domínio; manter como configuração única. Constantes de horário, idade, integrações e limiar de mapa são consumidas pelos módulos. |
| `src/coleta.py` | Fronteira de ingestão do CSV bruto do Fogo Cruzado; manter enquanto a fonte de entrada continuar CSV. |
| `src/limpeza.py`, `tratamento.py`, `features.py` | Transformações canônicas da pipeline; manter isoladas e testadas. |
| `src/estatisticas.py`, `graficos.py`, `series_temporais.py`, `clusterizacao.py`, `acao_policial.py` | Análises e visualizações reutilizáveis pelo batch e pelo notebook; manter como biblioteca. Algumas funções são auxiliares exploratórias e não aparecem no fluxo de `main.py`, mas fazem parte do uso analítico/notebook, então não foram removidas. |
| `src/integracao_externa.py` | Leitura/adaptação das fontes CTTU e SDS-PE; opcional quando os respectivos arquivos não existem. |
| `src/database.py` | Persistência canônica SQLite para snapshots analíticos e relatos; manter. |
| `src/relato_cidadao.py`, `protocolo_acompanhamento.py` | Domínio de relatos, verificação e consulta pública; manter como funcionalidade do produto. |
| `src/painel_gestao.py`, `mapa_interativo.py`, `relatorio.py` | Adaptadores de apresentação/exportação HTML, mapa e relatório; manter. |
| `scripts/gerar_dados_exemplo.py` | Gerador sintético para desenvolvimento, não dados reais; manter fora do fluxo de produção. |
| `scripts/migrar_artefatos_legados.py` | Migração de dados processados antigos para SQLite; manter até o período de transição terminar. |
| `scripts/preparar_powerbi.py` | Exportador sob demanda para interoperabilidade; CSV exportado não é fonte canônica. |
| `tests/` | Contrato comportamental da aplicação; manter e ampliar para módulos sem cobertura. |
| `notebooks/VigiaRecife.ipynb` | Narrativa exploratória, 103 células e ~48 mil caracteres de código/texto; conteúdo é distinto do batch. Manter, mas evitar versionar saídas grandes; atualmente há ~1,7 MB de outputs reproduzíveis embutidos. |
| `docs/metodologia.md` | Justificativa das decisões analíticas e de privacidade; manter como referência metodológica. |
| `docs/GUIA_POWERBI.md` | Procedimento para consumidor externo; manter enquanto Power BI for suportado. |
| `docs/ARQUITETURA_DADOS.md` | Contrato da persistência/modelo de dados SQLite; manter. |
| `docs/Vigia_Recife_Documentacao_Tecnica.docx`, `Vigia_Recife_Relatorio_Projeto.pdf` | Entregáveis documentais existentes; manter até comparar versão/conteúdo e confirmar que há cópia mais atual. Não são gerados pela pipeline. |
| `GUIA_TERMINAL.md` | Removido: duplicava setup, pipeline e testes já documentados no README. |
| `LICENSE` da raiz | Removida: arquivo vazio. A licença válida permanece em `VigiaRecife/LICENSE`. |

## Conteúdo removido do escopo

O diretório raiz `INFORMAÇÕES - GEVACZ/` foi excluído do repositório e da cópia de trabalho por solicitação explícita. A remoção abrangeu planilhas anuais de ovitrampas, arquivos de georreferenciamento e shapefiles de ovitrampas, estações disseminadoras e distritos sanitários. Esses materiais não são entradas da aplicação Vigia Recife.

## Dados e entregáveis

| Local | Conteúdo/retensão |
|---|---|
| `data/csv - eventos.csv`, `data/raw/`, `data/eventos.csv` | CSV de ocorrências principal e caminhos de compatibilidade/legado. A aplicação prioriza o arquivo completo na raiz de `data/`; manter fontes brutas separadas das saídas tratadas. |
| `data/database/vigia_recife.sqlite3` | Banco local não versionado. Fonte canônica para tabelas tratadas, agregações e relatos. Fazer backup antes de reprocessamentos ou migrações. |
| `data/processed/` | Mantido como diretório de compatibilidade para importação de CSV legado e exportação de protocolo JSON. Os quatro CSVs redundantes presentes foram removidos após constatar tabelas equivalentes no SQLite (mesmas contagens e colunas). |
| `data/powerbi/` | Cópias antigas do exportador, redundantes após a mudança de diretório; removidas. O destino atual e reproduzível é `data/exports/powerbi/`. |
| `data/exports/powerbi/` | CSVs temporários produzidos por solicitação para Power BI. Não versionar; podem ser recriados com o script de exportação. |
| `outputs/` | Relatório, painel, mapa e gráficos são artefatos de apresentação reproduzíveis; mantê-los no disco local, sem incluí-los no Git por padrão. |

## Limpeza do controle de versão

- `.venv_new/` tinha **1.509 arquivos** do ambiente Python 3.14 dentro do repositório. O ambiente foi removido da cópia de trabalho e do Git; dependências devem ser instaladas no `.venv` da aplicação a partir do `requirements.txt`.
- Arquivos temporários do Excel (`~$...`) e locks de GIS (`*.lock`, `*.sr.lock`) que estavam no acervo removido também deixaram o projeto.
- Arquivos de ambiente, cache, bancos, exportações e saídas geradas agora estão explicitamente excluídos do Git.

## Itens para próxima revisão

1. Limpar saídas embutidas do notebook (1,7 MB) após confirmar que a narrativa e o notebook sem outputs atendem ao uso didático.
2. Revisar versões dos documentos PDF/DOCX e registrar data/versão para evitar dois relatórios concorrentes.
3. Avaliar módulos de interface/relatos ainda sem cobertura automatizada e introduzir testes de integração da pipeline com banco em diretório temporário.
