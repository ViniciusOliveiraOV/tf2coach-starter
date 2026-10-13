# Backlog priorizado e critérios de aceite

**Método:** uma funcionalidade ponta a ponta por vez; prioridade P0 antes de P1; funcionalidades futuras não devem expandir o primeiro ticket. **Estado:** quase tudo PLANEJADO; não confundir documentação com implementação.

| ID | História / capacidade | Prioridade | Marco | Critério verificável |
|---|---|---|---|---|
| ENG-001 | Launcher Steam/TF2 com demos | P0 | M0 | `--dry-run` exibe flags; usuário verifica `.dem` gerada numa partida real |
| ENG-002 | Inventário local de `.dem` somente leitura | P0 | M0 | total de arquivos/tamanho correto e testes verdes |
| TF2-001 | Parser `.dem` real → JSON | P0 | M1 | JSON válido de arquivo real; métricas/cobertura/tempo medidos |
| TF2-002 | Normalização de eventos e métricas | P0 | M2 | fixtures/testes; não inferir dados ausentes |
| TF2-003 / US-001 | Relatório pós-sessão | P0 | M2 | sessão e fatos legíveis em texto; sem métrica inventada |
| TF2-004 / US-002 | Reconstrução tática contextual | P1 | M3 | reconstruir ao menos 1 confronto: sequência, posições/entidades disponíveis, lacunas |
| TF2-005 / US-003 | Contrafactuais táticos | P1 | M3 | 2 alternativas plausíveis com vantagens, riscos e incerteza, sem certeza ilusória |
| TF2-006 | Resenha textual com IA (opcional) | P1 | M3 | justificativas ligadas a eventos e limites de custo; não fabricar fatos |
| DEVOPS-001 | Uploader local seguro e automático | P1 | M4 | só arquivo comprovadamente fechado; checksum/verificação; retries; não apagar original prematuramente |
| DEVOPS-002 | Cloud mínima provisionada com Terraform | P1 | M4 | `plan` revisado; recursos privados, logs/custos/limpeza; `destroy` verificável |
| DEVOPS-003 | Worker / observabilidade | P1 | M4 | processamento assíncrono recuperável, logs mínimos e alarmes básicos |
| TF2-007 / US-004 | Recomendações específicas por sessão | P2 | M5 | até 3 hipóteses com evidências e teste sugerido |
| TF2-008 / US-005 | Histórico multi-sessão | P2 | M5 | padrões só após amostra suficiente; estatísticas contextualizadas |
| TF2-009 / US-006 | Crawler + base tática automática | P2 | M6 | **10–30 fontes**, fontes autorizadas, dedupe, atualizações e proveniência |
| TF2-010 | Busca/RAG com referências | P2 | M6 | cada afirmação externa remete à fonte e à data |
| UI-001 | Dashboard com gráficos | P3 | Futuro | métricas e histórico fiéis ao banco |
| TF2-011 | Vídeo/screenshots seletivos | P3 | Futuro | evidência incremental justifica custo e captura opt-in |
| TF2-012 | Treino em tempo real | P4 | Futuro | redesenho específico após validação/termos/risco |
| BIZ-001 | Contas múltiplas e monetização | P4 | Futuro | revisão de licenças, políticas de dados, segurança e demanda comercial |

## Definition of Done para cada ticket

- Necessidade observável, critérios de aceite e limite de escopo documentados.
- Implementação pequena com testes apropriados; execução comprovada ou bloqueio explicitado.
- Efeitos sobre segurança, custo, privacidade e armazenamento avaliados.
- Nenhuma ferramenta/infra sem motivação demonstrável.
- Evidências e limitações entregues; não declarar concluso sem executar/verificar.

## Sprint experimental de 1 dia

**Meta principal:** TICKET-001, alcançar uma demo real processada para JSON confiável e medir o custo básico do parsing. A captura pode levar mais caso não exista demo disponível. **Stretch goal:** primeiro relatório texto sem IA. **Fora de escopo:** cloud, RAG, IA multimodal, crawler, dashboard.

**Bloqueadores admissíveis:** jogo não instalado; nenhuma demo disponível; parser incompatível com versão real; indisponibilidade de ferramentas locais. Não mascarar bloqueadores criando dados falsos.

**Decisão de saída:** se o parser não extrair informações espaciais necessárias, não vender uma análise tática simulada. Experimentar fontes adicionais/demos diferentes ou renderização visual seletiva num ticket posterior.
