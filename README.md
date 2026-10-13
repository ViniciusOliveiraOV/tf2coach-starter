# TF2 Coach AI · Laboratório de Engenharia (v0.1)

**Status:** esqueleto inicial. **Usuários:** 1 (uso pessoal). **Produto comercial:** hipótese futura, não autorizado/implementado.

O objetivo é construir um treinador **pós-sessão** para Team Fortress 2 que reconstrua eventos de demos `.dem`, explique decisões táticas e, com evidências suficientes, sugira experimentos para partidas seguintes. Enquanto isso, o projeto serve de laboratório pragmático de engenharia, dados, DevOps, Terraform e segurança.

> **Há um primeiro relatório individual determinístico e local** a partir do JSON de demo; não há IA generativa, crawler, uploader para nuvem ou infraestrutura cloud. O launcher e o sincronizador preservam demos originais; nenhuma demo é enviada ou removida automaticamente.

## Início rápido no Arch Linux

Pré-requisitos da primeira etapa: Steam com TF2 instalado, `bash`, `python3`, `setsid` (util-linux) e (opcionalmente) `git`.

```bash
unzip tf2coach-starter.zip
cd tf2coach-starter
python3 -m unittest discover -s tests -v
./scripts/tf2coach --dry-run
./scripts/tf2coach
```

## Interface web local

O frontend React/TypeScript reproduz a referência retrô e funciona sem o backend. Em outra sessão de terminal:

```bash
npm ci
npm test
npm run build
npm run local
```

`npm run local` gera o build e abre o site privado em `http://127.0.0.1:8765/`. O catálogo local associa demos e vídeos, produz uma projeção JSON individual e alimenta a seção REPLAYS. Dados de partidas e vídeos permanecem privados e não entram no build. Novas demos fechadas em `data/demos/` são processadas quando o site abre ou atualiza, desde que `tf-demo-parser` 0.7.1 esteja disponível. Consulte [`docs/FRONTEND.md`](docs/FRONTEND.md) para associar vídeos de nomes diferentes, desenvolver com Vite e entender as limitações de privacidade.

`IMPORTAR JSON` aceita a projeção individual anonimizada do resultado de `build_analysis()` em `scripts/analyze_demo.py` (campos como `map`, `duration_seconds`, `metrics`, `weapon_counts`, `event_window` e `rounds`). Não selecione o JSON bruto do parser: ele contém nomes, SteamIDs e chat. A interface mantém somente os campos reconhecidos e não exibe texto livre, identidade do jogador ou conteúdo de chat. O contrato e limitações estão em [`docs/FRONTEND.md`](docs/FRONTEND.md).

O launcher pede à Steam que abra o TF2 com a gravação automática de `.dem` e inicia o sincronizador local. Em partida compatível, o jogo grava sob `tf/tf2coach` **dentro da biblioteca Steam**; o sincronizador localiza bibliotecas secundárias consultando `libraryfolders.vdf`.

O sincronizador, no Linux, verifica em `/proc` os descritores acessíveis ao usuário que iniciou TF2 (o launcher executa Steam e jogo como o usuário atual); não usa apenas tempo sem alterações. Antes de publicar, revalida tamanho, metadados e SHA-256. A cópia temporária só recebe o nome final depois da verificação; colisões não sobrescrevem arquivos. Os originais nunca são alterados.

As cópias ficam em `data/demos/`, ignorada pelo Git, com limite rígido de 2 GiB no diretório. Ao atingir o limite, novas cópias são pausadas e um aviso é exibido; nada é removido automaticamente. O processo permanece ativo no terminal para acompanhar a partida: use `Ctrl+C` para encerrá-lo. Isso não encerra nem altera os arquivos do jogo.

Para testar sem iniciar TF2/Steam:

```bash
python3 -m unittest discover -s tests -v
./scripts/tf2coach --dry-run
```

`--dry-run` mostra o comando da Steam, o destino e o sincronizador, sem iniciar nenhum deles. Para consultar manualmente uma pasta de demos:

```bash
python3 scripts/demo_inventory.py --dir '/CAMINHO/Team Fortress 2/tf/tf2coach' --json
```

O inventário existente marca arquivos recentes como `possivelmente_em_gravacao`: é apenas uma heurística; o sincronizador não a usa como prova de fechamento.

Para gerar um relatório individual depois de produzir/validar o JSON com `tf-demo-parser`:

```bash
python3 scripts/analyze_demo.py data/parsed/<resumo>.json
```

O relatório vai para `data/reports/` e permanece privado/ignorado pelo Git. A seleção padrão usa o POV quando o nick do cabeçalho encontra uma identidade única; caso contrário, informe `--steam-id <id>`. O script preserva relatórios existentes; use outro `--output` ou passe `--force` para substituição explícita. Veja [`docs/VALIDACAO_DEMO.md`](docs/VALIDACAO_DEMO.md) e a skill local [`tf2-demo-analysis`](.agents/skills/tf2-demo-analysis/SKILL.md) para schema, privacidade e limitações.

Para tornar o launcher um comando do shell (opcional):

```bash
mkdir -p "$HOME/.local/bin"
ln -s "$(pwd)/scripts/tf2coach" "$HOME/.local/bin/tf2coach"
# Verifique se ~/.local/bin está no PATH e então execute: tf2coach
```

Não use `sudo`. Não execute scripts desconhecidos baixados da internet. Não comite demos, credenciais ou relatórios privados.

## O que está dentro

- [`docs/PROJETO.md`](docs/PROJETO.md): documento principal, objetivos, fases, arquitetura e decisões.
- [`docs/BACKLOG.md`](docs/BACKLOG.md): histórias, prioridades e critérios de aceite.
- [`docs/SEGURANCA_E_CUSTOS.md`](docs/SEGURANCA_E_CUSTOS.md): requisitos mínimos de segurança, privacidade e custos.
- [`docs/adr/`](docs/adr): decisões arquiteturais (ADRs).
- [`CODEX_PROMPT.md`](CODEX_PROMPT.md): prompt para iniciar o trabalho.
- [`AGENTS.md`](AGENTS.md): regras que o Codex deve observar.
- [`scripts/tf2coach`](scripts/tf2coach): launcher da Steam/TF2 e do sincronizador local; `--dry-run` não inicia processos.
- [`scripts/demo_sync.py`](scripts/demo_sync.py): descoberta de bibliotecas Steam, verificação de demos concluídas e cópia local limitada/verificada.
- [`scripts/demo_inventory.py`](scripts/demo_inventory.py): inventário somente leitura.
- [`scripts/analyze_demo.py`](scripts/analyze_demo.py): relatório individual a partir do JSON existente do parser.
- [`.agents/skills/tf2-demo-analysis/SKILL.md`](.agents/skills/tf2-demo-analysis/SKILL.md): procedimento reutilizável do Codex para análise de demos.
- [`infra/terraform/local/`](infra/terraform/local): exercício **local** de plan/apply, sem recurso cloud.

## Fluxo do laboratório

- **TICKET-001:** parser 0.7.1 validado com demo real; veja `docs/VALIDACAO_DEMO.md`.
- **TICKET-002:** relatório individual local e determinístico, com fixture anonimizada e skill Codex em `.agents/skills/tf2-demo-analysis/`.
- Para análise reproduzível, use o JSON do parser e `python3 scripts/analyze_demo.py <resumo.json>`. O comando não substitui relatórios existentes sem `--force` e nunca substitui o JSON de entrada.

**Não autorize `terraform apply` numa conta cloud, novos serviços pagos, upload para terceiros ou remoção automática de arquivos sem uma decisão sua.**

## Fontes úteis

- Valve / TF2: https://www.teamfortress.com/post.php?id=22132
- TF2 demo parser (Rust): https://github.com/yep-tf2/tf2-demo-parser
- Documentação do pacote: https://docs.rs/crate/tf-demo-parser/latest
- Steam, opções de inicialização: https://help.steampowered.com/pt/faqs/view/7D01-D2DD-D75E-2955

Estes são links de consulta; as respectivas ferramentas/versões devem ser verificadas novamente na implementação.
