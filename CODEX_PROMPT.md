# Prompt pronto para o Codex · Primeira sessão

Você está no repositório **TF2 Coach AI** (Arch Linux). Leia `AGENTS.md`, `README.md`, `docs/PROJETO.md`, `docs/BACKLOG.md`, `docs/SEGURANCA_E_CUSTOS.md` e `docs/TICKET-001.md`.

**Sua tarefa nesta sessão é somente o TICKET-001.** O objetivo é verificar o launcher, localizar uma demo `.dem` real (sem varrer a máquina indiscriminadamente), medir seu tamanho e validar uma ferramenta de parsing capaz de gerar JSON. Não construa IA, crawler, frontend, upload, banco ou infraestrutura cloud ainda. Não assuma que arquivos `.dem` contêm todas as entidades, coordenadas ou contextos necessários para inferir decisões táticas.

Procedimento:

1. Faça um diagnóstico local não destrutivo: detecte `steam`, `python3`, `cargo` e possíveis diretórios de instalação do TF2. Se não encontrar uma demo, explique como gravá-la e encerre como bloqueio de dados reais, sem fabricar uma.
2. Execute os testes atuais e `./scripts/tf2coach --dry-run`; valide e corrija pequenos problemas demonstrados por testes.
3. Com demo disponível, compare tamanho real, duração se recuperável e custo computacional do parsing. Avalie o parser Rust `yep-tf2/tf2-demo-parser` e eventuais alternativas: versão/commit, licença, saída JSON, compatibilidade com demos atuais. Não instale globalmente; solicite permissão se precisar baixar código de terceiros.
4. Implemente um wrapper mínimo e testável de leitura/normalização **somente se** houver parser/dado válido e pré-requisitos. Salve relatórios locais na pasta ignorada `data/`; jamais altere arquivos originais.
5. Entregue evidências concretas e matriz de capacidades: confirmado por demo, parcial, desconhecido, não disponível. Liste explicitamente lacunas para análise espacial, visibilidade e contrafactual.

Critérios para encerrar: testes verdes; caminho das demos documentado; pelo menos um JSON válido extraído de arquivo real (ou bloqueio objetivo documentado); tempo/tamanho medidos quando aplicável; nenhuma credencial ou demo enviada; nenhum custo criado.

Trabalhe com o espírito de *The Pragmatic Programmer*: pequenas entregas verificáveis, nada de arquitetura especulativa. **Não execute `terraform apply`, não configure contas cloud e não exclua arquivos.**

Ao final mostre: o que foi validado, o que não pôde ser validado, como reproduzir e qual o próximo ticket recomendado.
