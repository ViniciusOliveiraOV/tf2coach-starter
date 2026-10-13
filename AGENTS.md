# Regras para agentes de código (Codex e equivalentes)

Leia **README.md**, **docs/PROJETO.md**, **docs/BACKLOG.md** e **docs/SEGURANCA_E_CUSTOS.md** antes de alterações.

## Não negociável

1. Respeite o escopo do ticket corrente. Antes de introduzir uma tecnologia, explique a necessidade concreta e alternativa simples. Sem overengineering.
2. Não instale pacotes globalmente; em Arch Linux, respeite Python gerenciado pelo sistema. Use venv somente se necessário.
3. Não execute `terraform apply` de cloud, não crie recursos pagos, não faça upload de demos, não conecte APIs pagas sem autorização explícita.
4. Nunca exclua ou modifique demos originais, configurações Steam/TF2, jogos, dados pessoais e credenciais. Não rode comandos destrutivos/limpeza sem confirmação específica.
5. Não faça scraping indiscriminado. Regras de sites, robots.txt, autorização, licenças, frequência e privacidade são pré-condições.
6. Não adicione multiplayer, cobrança, painel avançado, LLM, RAG, workers e filas antes de demonstração de necessidade. O MVP é pós-sessão e para um usuário.
7. Não invente métricas que o parser não traz. Separe fatos observados, inferências e hipóteses. Um `.dem` POV não equivale a estado completo do servidor.
8. Faça testes para alterações comportamentais; não burle testes. Documente limitações e evidências de sucesso.
9. Segredos via ambiente/config segura, jamais hardcoded. Não publique demos, SteamID, nomes de jogadores ou dados de sessão.
10. Não incorpore ferramentas externas sem conferir a origem, manutenção e compatibilidade, inclusive licenças.

## Fluxo pragmático

- Leia o ticket e faça no máximo 3 perguntas se houver bloqueio real; de resto assuma defaults conservadores.
- Apresente plano curto (3 a 5 ações). Execute e teste.
- Resuma arquivos alterados, comandos executados, resultados, riscos e próximo passo.
- Pequenos commits lógicos; não altere arquivos fora do escopo.
- Corrija janelas quebradas quando surgirem; quando inviável, registre dívida técnica com impacto.

**Primeiro ticket:** `docs/TICKET-001.md`.
