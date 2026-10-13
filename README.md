# TF2 Coach AI · Laboratório de Engenharia (v0.1)

**Status:** esqueleto inicial. **Usuários:** 1 (uso pessoal). **Produto comercial:** hipótese futura, não autorizado/implementado.

O objetivo é construir um treinador **pós-sessão** para Team Fortress 2 que reconstrua eventos de demos `.dem`, explique decisões táticas e, com evidências suficientes, sugira experimentos para partidas seguintes. Enquanto isso, o projeto serve de laboratório pragmático de engenharia, dados, DevOps, Terraform e segurança.

> **Não há analista, crawler, uploader ou infraestrutura cloud funcionando neste ZIP.** Existem o launcher mínimo, um inventário local somente leitura, testes e documentos para o Codex iniciar o desenvolvimento por etapas. Não enviamos nem apagamos suas demos.

## Início rápido no Arch Linux

Pré-requisitos da primeira etapa: Steam com TF2 instalado, `bash`, `python3` e (opcionalmente) `git`.

```bash
unzip tf2coach-starter.zip
cd tf2coach-starter
python3 -m unittest discover -s tests -v
./scripts/tf2coach --dry-run
./scripts/tf2coach
```

O último comando pede à Steam que abra o TF2 com a gravação automática de `.dem` habilitada. **Teste primeiro** em uma partida compatível e use `ds_status` no console do jogo. O comportamento exato pode variar com versão do jogo/servidor e opções configuradas na Steam.

Os arquivos `.dem` vão para uma subpasta `tf2coach` **no diretório de jogo** (normalmente `.../Team Fortress 2/tf/tf2coach`), **não neste repositório**. Se o jogo estiver instalado numa biblioteca secundária, o caminho será outro.

Localize a instalação pelo menu da Steam: Biblioteca → TF2 → Gerenciar → Explorar arquivos locais.

```bash
# Depois que houver uma demo, indique o diretório correto:
python3 scripts/demo_inventory.py --dir '/CAMINHO/Team Fortress 2/tf/tf2coach'
# Inventário estruturado, sem salvar/copiar nada:
python3 scripts/demo_inventory.py --dir '/CAMINHO/Team Fortress 2/tf/tf2coach' --json
```

O inventário marca arquivos modificados recentemente como `possivelmente_em_gravacao`: é apenas uma **heurística**, não prova de que estão fechados. Nenhum processo deve enviar/remover arquivos baseado apenas nesse sinal.

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
- [`scripts/tf2coach`](scripts/tf2coach): launcher básico e modo dry-run.
- [`scripts/demo_inventory.py`](scripts/demo_inventory.py): inventário somente leitura.
- [`infra/terraform/local/`](infra/terraform/local): exercício **local** de plan/apply, sem recurso cloud.

## Primeiro trabalho com o Codex

1. Extraia o ZIP e entre na pasta.
2. Inicialize versionamento com `git init` e faça commit do esqueleto.
3. Leia `CODEX_PROMPT.md` e envie seu conteúdo ao Codex aberto **neste diretório**.
4. Passe pelo primeiro ticket: localizar demo real, medir tamanho/tempo e validar o parser JSON (sem cloud e sem IA).
5. Só passe à etapa seguinte se os critérios de aceite estiverem satisfeitos.

**Não autorize `terraform apply` numa conta cloud, novos serviços pagos, upload para terceiros ou remoção automática de arquivos sem uma decisão sua.**

## Fontes úteis

- Valve / TF2: https://www.teamfortress.com/post.php?id=22132
- TF2 demo parser (Rust): https://github.com/yep-tf2/tf2-demo-parser
- Documentação do pacote: https://docs.rs/crate/tf-demo-parser/latest
- Steam, opções de inicialização: https://help.steampowered.com/pt/faqs/view/7D01-D2DD-D75E-2955

Estes são links de consulta; as respectivas ferramentas/versões devem ser verificadas novamente na implementação.
