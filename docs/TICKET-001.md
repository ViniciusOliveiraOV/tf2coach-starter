# TICKET-001 · Validação do caminho `.dem` → JSON

**Prioridade:** P0  
**Objetivo de negócio:** determinar se os dados disponíveis permitem fundamentar a análise de jogo sem gravar vídeo.  
**Limite:** 1 usuário; sem cloud/IA; não modificar Steam/TF2 diretamente sem pedido explícito.

## Passos

1. Verificar `./scripts/tf2coach --dry-run` e ativar/confirmar gravação no TF2 (`ds_status`).
2. Localizar arquivo `.dem` produzido; registrar local, tamanho e capacidade livre observada, sem comitar conteúdo.
3. Testar ao menos um parser mantido, em ambiente isolado e com aprovação quando demandar downloads.
4. Extrair uma saída JSON real, verificar cabeçalhos, eventos, participantes e limitações.
5. Catalogar recursos necessários para a análise tática: mudanças de classe, mortes, posições/ticks, sentries, linha de visão (não presumir disponibilidade), contexto do time.
6. Escrever resultados em `docs/VALIDACAO_DEMO.md`, com comandos reproduzíveis e comparativo entre fatos extraídos e inferências.

## Definition of Done

- Testes automatizados existentes passam.
- Demonstrado `launcher --dry-run`, com caminho da pasta corretamente entendido.
- Pelo menos uma demo analisada, ou bloqueio declarado se não existir.
- Se demo analisada: JSON parseado, tamanho e tempo medidos, nenhuma métrica inventada.
- Nenhum dado pessoal publicado ou enviado; nenhum recurso cloud criado.

**Não incluído:** vídeo, screenshots, análises de IA, RAG, Terraform cloud, upload, banco, frontend.
