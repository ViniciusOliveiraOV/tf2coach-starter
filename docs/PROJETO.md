# TF2 Coach AI · Documento mestre

**Versão:** 0.1 | **Data:** 13/10/2026 | **Status:** requisitos refinados; funcionalidade de análise ainda não validada.

## 1. Visão

Criar um **treinador pessoal pós-sessão** de Team Fortress 2. O sistema processará gravações `.dem`, reconstruirá eventos e contexto espacial/temporal quando os dados permitirem, apresentará diagnóstico factual e hipóteses táticas e oferecerá recomendações de melhoria baseadas no histórico. Paralelamente, servirá como laboratório demonstrável de engenharia (DevOps, Terraform, processamento assíncrono, segurança, observabilidade e dados).

**Nesta fase:** uso local/privado, somente o proprietário, não comercial. No futuro poderá ser produto, condicionando a termos de Valve/Steam, licenças e validação técnica. **Tempo real:** fora de escopo, possível evolução futura.

## 2. Requisitos do produto

- Sessões de até **2 horas** com múltiplas rodadas e mapas; relatórios ao **final da sessão**.
- Lançador `tf2coach` inicia TF2 via Steam com sistema de demos automático; em partidas compatíveis, gera `.dem` em `tf/tf2coach`, **dentro da instalação do jogo**, não dentro do Git.
- Arquivos `.dem` **não são vídeos**. São gravações Source que podem conter eventos e estados de rede. Demos POV de cliente não garantem conhecimento de tudo que acontece no servidor, de visibilidade ou de intenções humanas.
- **Análise contextual:** class changes, deslocamento, uso de habilidades, eliminações/mortes, sentries e outros objetos presentes; perspectiva do jogador e eventos conhecidos naquele instante.
- **Análise factual x inferencial x contrafactual:** distinguir ocorrência registrada, interpretação e estratégia alternativa plausível. Nunca prometer que um contrafactual teria acontecido.
- **Evolução histórica:** comparar sessões para identificar padrões como trocas frequentes de classe, decisões frente à composição das equipes e exposição repetida a riscos. Evitar conclusões sobre amostras pequenas.
- **Recomendações finais:** no máximo 3 hipóteses testáveis, ligadas a dados da sessão e, posteriormente, fontes externas verificáveis.
- **Base tática automatizada (futura):** crawler responsável, de 10 a 30 fontes qualificadas, descoberta/atualização incremental, proveniência, data, categoria, licença, confiabilidade e distinção entre jogos casuais e competitivos. Fonte oficial ≠ opinião popular. RAG só quando necessário.
- **Visualização (futura):** texto primeiro; dashboard React e gráficos quando os dados estiverem estabelecidos. Captura de vídeo/screenshots **apenas sob demanda** e se demo for insuficiente.

## 3. Fluxos arquiteturais

### 3.1 Primeira prova de valor (local, sem nuvem)

```text
Steam/TF2 --(ds_enable 2)--> arquivo .dem no gamedir
                                  |
                           inspeção local
                                  |
                            parser testado
                                  |
                         JSON + relatório básico
```

Nesta versão starter, **launcher, inventário, parsing de demo real e relatório individual determinístico local** estão implementados. TICKET-001 validou `tf-demo-parser` e documentou o JSON observado; TICKET-002 calcula contagens individuais somente dos registros verificáveis e grava Markdown privado em `data/reports/`. Não há IA generativa, análise espacial ou conclusão tática automatizada nesta etapa.

### 3.2 Arquitetura-alvo incremental (não implementada)

```text
TF2 no Arch
   -> demo concluída no disco (pequena janela de buffer)
   -> uploader local independente, idempotente (futuro)
   -> armazenamento privado e temporário (cloud, futuro)
   -> job sob demanda -> worker de parsing -> métricas estruturadas
   -> armazenamento resumido de sessões (SQLite primeiro, DB gerenciado só se justificar)
   -> regras táticas + RAG de fontes confiáveis, se necessário
   -> LLM pós-sessão com evidência/citações
   -> relatório e dashboard, se necessário
```

**Componentes futuros não exigem serviços separados desde o começo.** Fila pode começar simples com jobs persistidos, worker como tarefa única, e migrar quando houver números que o justifiquem. Não há requisito de Kubernetes.

### 3.3 Pipeline de conhecimento (futuro)

```text
Sementes confiáveis + descoberta controlada (10-30 fontes)
  -> validar acesso permitido/robots/termos/licenças
  -> extração incremental, dedupe, normalização
  -> catálogo (URL, data, categoria, contexto, licença, grau de evidência)
  -> busca textual/RAG
  -> fundamentação de hipótese tática com fontes
```

Não incorporar Reddit ou transcrições de terceiros sem verificar permissões aplicáveis e uso permitido. Conteúdo competitivo e casual precisa ser distinguido.

## 4. Dados e armazenamento

- A `.dem` é **dado bruto temporário**; relatório e métricas estruturadas são o histórico desejável.
- **Meta inicial de buffer local: 2 GiB** para o TF2 Coach, sendo um **limite de projeto**, não uma garantia que o jogo ou scripts impedirão gravações maiores. Há aproximadamente 50 GB livres relatados na home (medição anterior, não confirmada agora). Nunca pressupor esse número para decisões automáticas.
- Nunca apagar arquivo original por idade ou por heurística. Primeiro implementar confirmação real de fim de gravação, envio íntegro, confirmação remota, política de retenção e recuperação de falhas.
- Verificar disco antes/durante a sessão e notificar se perto do limite. Política de queda de internet deve preservar dados, sinalizar risco e **evitar apagar não enviados**.
- Armazenamento remoto deve ser privado, criptografado e temporário. Registros e relatórios guardados pelo tempo decidido pelo usuário; custos medidos por sessão. Definir orçamento antes de cloud.
- Não capturar vídeo contínuo de duas horas por padrão. Se for necessária análise visual, escolher eventos/trechos específicos e comparar custo e ganho de precisão.

## 5. Ordem de implementação

**M0 · Starter (agora):** estrutura Git, README, launcher, inventário de arquivos, testes e documentos. Não configura Steam do usuário automaticamente.

**M1 · Validação de demo:** gravar/obter `.dem` real, validar parser, gerar JSON, medir duração/tamanho/tempo de processamento, matriz de dados realmente disponíveis. **Gate decisório:** dados permitem análise tática? Se não, experimentar visual seletivo antes de prometer coaching.

**M2 · Primeiro relatório pós-sessão:** normalizar dados reais, relatório textual local sem IA, dois ou três eventos explicados e testes.

**M3 · Analista por evidência:** acrescentar regras táticas; distinguir fatos x inferências x contrafactuais; LLM opcional apenas para redação, com custo/cotas; não inventar observações.

**M4 · Captura/upload em nuvem:** watcher/uploader idempotente, upload seguro, checagem de integridade, retry, limites, privacidade, retenção, falhas simuladas; Terraform para recursos realmente necessários e GitHub Actions quando viável. **Nenhum acesso cloud automático no starter.**

**M5 · Histórico e recomendações:** armazenar métricas resumidas e comparar sessões; regras de evidência mínima; recomendações experimentais.

**M6 · Crawler tático controlado e busca:** 10-30 fontes, atualização incremental, auditoria, contextualização por versão/mapa/modo, citações por recomendação; avaliação de utilidade/custo.

**Futuro condicionado:** dashboard, vídeo seletivo, análises ao vivo, múltiplos usuários e monetização. Cada fase exige nova decisão e, quando aplicável, revisão jurídica/contratual.

## 6. Critérios de qualidade

- Cada fase entrega uma funcionalidade verificável, não somente infraestrutura.
- Testes de código e cenários de falha (rede, disco, parser, demo incompatível) conforme o comportamento implementado.
- Observabilidade mínima: tempo de processamento, erro, tamanho, custo quando houver recursos pagos; evitar dados pessoais em logs.
- Segurança incremental desde o início: nenhum segredo hardcoded, uploads privados, limites de acesso e custo; não deixar portas desnecessariamente públicas.
- Documentar **por que** ferramentas entram. Comparar alternativa simples e alternativa complexa.
- *The Pragmatic Programmer*: DRY sem abstração excessiva, testes, responsabilidade por janelas quebradas e entregas pequenas tipo tracer bullets.

## 7. Questões técnicas ainda abertas (não inventar respostas)

1. Cobertura real do `.dem` POV no TF2 atual: posições, estado de construções, mira, visibility/occlusion, mudanças de classe e eventos de round.
2. Como delimitar com precisão uma sessão de 2h e arquivos ainda abertos.
3. Escolha do provedor cloud e custo por GiB/upload/compute/LLM. Terraform deve refletir recursos concretos, não exercícios desnecessários.
4. É necessário renderizar trechos de demo para visão? Qual hardware/infra? Testar em pequeno escopo.
5. Fontes/termos/licenças para crawler e possível produto comercial.
6. Métricas táticas devem controlar mapa, modo casual/competitivo, composição, duração e qualidade dos dados; não usar K/D isolado para concluir qualidade da jogada.

## 8. Referências técnicas

- https://www.teamfortress.com/post.php?id=22132 (Demo Support)
- https://github.com/yep-tf2/tf2-demo-parser (parser Rust)
- https://docs.rs/crate/tf-demo-parser/latest (documentação)
- https://help.steampowered.com/pt/faqs/view/7D01-D2DD-D75E-2955 (opções de inicialização)
- https://wiki.teamfortress.com/ (wiki comunitária oficial, com diferenças entre conteúdo oficial e da comunidade)
- https://developer.hashicorp.com/terraform/language (Terraform)

## 9. Definição objetiva de sucesso

**Primeiro sucesso de engenharia:** JSON verificável extraído de uma demo **real**, com limitações identificadas.  
**Primeiro sucesso de produto:** relatório factual reproduzível de uma situação real.  
**Primeiro sucesso de coaching:** recomendação testável, contextualizada e ancorada em evidências.  
**Primeiro sucesso DevOps:** pipeline de ponta a ponta seguro, monitorável, reversível e com custo mensurado.  
**Nenhum desses resultados foi reivindicado como concluído neste ZIP.**
