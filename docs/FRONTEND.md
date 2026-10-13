# Interface web local

## Desenvolvimento

Node.js e npm devem estar instalados localmente. Execute na raiz:

```bash
npm ci
npm test
npm run build
npm run local
```

`npm run local` abre o build em `http://127.0.0.1:8765/` por um servidor Python da biblioteca padrão, limitado a `127.0.0.1`. Para editar o frontend com Vite, execute `python3 -m scripts.replay_pipeline serve` em outro terminal e então `npm run dev`; o proxy `/api` do Vite usa esse servidor local. O bundle não contém demos, vídeos, relatórios privados ou identificadores.

## Catálogo local de replays

Quando há uma demo processada localmente, REPLAYS mostra apenas sua projeção individual validada. Sem vídeo associado, a interface indica essa ausência. O parser gera métricas a partir da `.dem`; o vídeo é somente a mídia de reprodução. Dados e correções de associações de uma sessão concreta ficam no catálogo privado em `data/replays/`.

Para associar outra gravação cujo nome não seja igual ao da demo:

```bash
python3 -m scripts.replay_pipeline register data/demos/AAAA-MM-DD_HH-MM-SS.dem --video '/CAMINHO/GRAVACAO.mp4'
python3 -m scripts.replay_pipeline unpair data/demos/AAAA-MM-DD_HH-MM-SS.dem
```

O comando lê o JSON privado já existente em `data/parsed/`; se faltar, executa o `parse_demo` de `tf-demo-parser` 0.7.1 em `/tmp/tf-demo-parser-install/bin/parse_demo`. Um caminho diferente pode ser fornecido com `--parser` ou `TF2COACH_PARSER`. Ele reutiliza `build_analysis()` do TICKET-002, preserva o Markdown existente, cria somente a projeção segura em `data/replays/` e rejeita uma associação conflitante.

Ao abrir ou atualizar o site local, o servidor verifica novas demos fechadas em `data/demos/` e processa as que faltam. Ele associa automaticamente um vídeo apenas quando existe `data/videos/<mesmo nome da demo>.mp4` ou `.webm`; nomes diferentes exigem o comando explícito acima. O catálogo mostra a partida mesmo sem vídeo, indicando a ausência da gravação. Nenhum arquivo original é removido ou substituído.

O servidor entrega ao navegador apenas os campos individuais permitidos e um endereço local para o MP4, com suporte a requisições parciais de vídeo. Caminhos absolutos, SteamIDs, nicks, chat e o JSON bruto ficam fora da resposta e do build. Os arquivos privados em `data/` continuam ignorados pelo Git; o vídeo permanece em sua localização original. Este site local não deve ser exposto na rede sem uma revisão específica de acesso e privacidade.

## Importação de relatório

O seletor local aceita JSON de até 2 MB com a projeção anonimizada do objeto devolvido por `build_analysis()` em `scripts/analyze_demo.py`. `schemaVersion` é opcional; se presente, precisa ser `1`.

O campo `selection` é obrigatório e aceita somente os rótulos genéricos emitidos por `build_analysis()` (“POV do cabeçalho, correspondência única” ou “SteamID informado explicitamente”); isso impede aceitar o JSON bruto do parser por engano. Os demais campos reconhecidos são `map`, `duration_seconds`, `metrics` (`kills`, `deaths`, `assists`, `self_eliminations`), `weapon_counts`, `event_window` (`first_tick`, `last_tick` e os tempos relativos opcionais), `events` individuais (`tick`, papéis permitidos e `weapon`) e `rounds` (`winner`, `length_seconds`). Cada campo é validado por tipo e faixa; métricas e contagens precisam ser inteiros não negativos. A interface exibe eventos apenas como participações do jogador selecionado pelo analisador e separa rodadas como contexto global. Campos adicionais, inclusive `users` e `chat`, não são copiados nem renderizados.

O importador não lê diretamente a saída bruta de `parse_demo`; ela inclui identidades e chat, e não é um relatório individual. O relatório Markdown atual do TICKET-002 também não é JSON importável. Para gerar dados para a interface, exporte explicitamente apenas a projeção segura do objeto de análise. A interface não recalcula métricas.

Quando o Vite roda em modo de desenvolvimento, partidas ainda sem registro podem aparecer como placeholders fictícios, identificados como “DADOS DE DEMONSTRAÇÃO”. Um replay real do catálogo substitui o placeholder da mesma data. Arquivos importados são processados em memória no navegador e não são enviados a serviço externo.

## Mídia do footer

O footer exibe as três animações das páginas Tenor fornecidas no ticket. As páginas e os arquivos diretos responderam HTTP 200 em 13/10/2026. O HTML público confirma GIFs de 200×200, 36×36 e 328×246 pixels; dimensões e proporções são mantidas no layout, que apenas limita o tamanho visual máximo.

Os arquivos permanecem hospedados no Tenor: não foi possível confirmar uma licença que autorize redistribuir cópias locais. Cada GIF é um link para sua página de origem, identificado por nome acessível, sem legenda visual sob a imagem. Isso requer conexão com `media1.tenor.com`/`media.tenor.com` e comunica o endereço IP do visitante a esse serviço. Se a hospedagem dos arquivos ou os termos mudarem, as animações podem deixar de carregar. Os posters PNG públicos do Tenor substituem os GIFs quando `prefers-reduced-motion: reduce` estiver ativo. Não se usa API nem iframe.

O título e a navegação usam a fonte Frijole, distribuída localmente em `public/assets/fonts/` com sua licença OFL. Quando há conteúdo além da altura de uma análise, sua barra clara é uma barra de rolagem nativa: arraste a barra à esquerda, use a roda do mouse sobre o bloco ou foque o bloco e use as teclas de rolagem. O conteúdo geral usa outra barra nativa no lado direito quando excede a altura da janela.

Para manter os GIFs, confira os metadados `og:image` e `og:image:width`/`height` das mesmas três páginas, atualize `footerGifs` em `src/ui/App.tsx` com URL animada, poster, texto alternativo e página de origem, e rode `npm test` e `npm run build`. Não copie os arquivos para `public/` sem verificar primeiro os direitos de redistribuição; não substitua as referências por GIFs semelhantes.
