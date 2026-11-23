# Arquitetura de dados e persistência

## Princípio de armazenamento

SQLite é a fonte canônica local para resultados analíticos e relatos. O runtime usa `sqlite3` da biblioteca padrão e Pandas para a fronteira tabular; não há servidor para instalar ou manter. O banco padrão é `data/database/vigia_recife.sqlite3`.

CSV permanece somente nas fronteiras de intercâmbio: ingestão de fontes (a aplicação prioriza `data/csv - eventos.csv`, depois aceita `data/raw/eventos.csv` e `data/eventos.csv`) e exportação voluntária para ferramentas externas (`data/exports/`). `VIGIA_CSV_EVENTOS` permite configurar explicitamente a entrada.

## Tabelas geradas

| Tabela | Conteúdo | Escrita |
|---|---|---|
| `eventos_tratados` | Registros analisados após anonimização de endereço e arredondamento das coordenadas | Execução da pipeline |
| `bairros_cluster` | Perfil comportamental e cluster atribuído por bairro | Pipeline, quando há bairros elegíveis |
| `acao_policial_por_bairro` | Contagens e percentual de ação policial agregados por bairro | Execução da pipeline |
| `base_integrada` | Registros Fogo Cruzado e fontes externas disponíveis | Quando o resultado integrado não está vazio |
| `relatos` | Protocolo, status, bairro, tipo e payload JSON do relato, inclusive histórico comunitário | Operações de relato/status |

As tabelas analíticas são snapshots substituídos na execução, não histórico de execuções. Relatos persistem entre execuções. Alterações futuras de esquema devem ser versionadas com migrações explícitas antes de acrescentar aplicações concorrentes ou API.

## Importação e exportação

- `python scripts/migrar_artefatos_legados.py`: importa CSVs processados e `relatos.json` de versões anteriores. Não apaga nem altera os arquivos de origem.
- `python scripts/preparar_powerbi.py`: lê tabelas SQLite e gera CSVs UTF-8 BOM em `data/exports/powerbi/` para consumo no Power BI.
- `src/database.py`: API de persistência. Identificadores de tabela são validados; dados são enviados por parâmetros e transações SQLite.

## Operação e segurança

- O arquivo SQLite, dados brutos, dados exportados e saídas são ignorados pelo Git.
- `eventos_tratados` é anonimizada pelo fluxo principal, mas outras tabelas integradas podem conter dados de localização e precisam ser revisadas antes de compartilhamento.
- Os relatos contêm descrição livre e coordenadas opcionais; proteger arquivo, backup e acesso conforme a política aplicável. SQLite local não implementa autenticação, criptografia em repouso, trilha imutável nem concorrência multiusuário de aplicação.
- Backup deve copiar o banco com a aplicação parada ou usar a API de backup do SQLite. Não sincronizar o arquivo aberto por múltiplos processos em pastas cloud como substituto de banco multiusuário.
- Ao publicar resultados, aplicar agregação e limiares mínimos e revisar risco de reidentificação, conforme `metodologia.md`.
