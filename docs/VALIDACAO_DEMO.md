# Validação de demos e schema observado

A primeira validação local usou tf-demo-parser 0.7.1 e produziu JSON sintaticamente válido de uma demo real. Os valores, horários, hashes e relatórios dessa sessão ficam apenas em data/private-notes/VALIDACAO_DEMO.md e nas demais pastas privadas de data/. Este documento público registra o procedimento e os campos necessários para reproduzi-lo com uma demo própria.

## Parser

- Pacote: https://crates.io/crates/tf-demo-parser/0.7.1
- Repositório informado pelo pacote: https://codeberg.org/demostf/parser
- Licença declarada no pacote: MIT OR Apache-2.0.
- Instalação isolada: cargo install tf-demo-parser --version 0.7.1 --locked --root /tmp/tf-demo-parser-install
- A CLI parse_demo recebe o caminho de uma demo e escreve JSON no stdout.

## Procedimento local

1. Mantenha a demo original em data/demos/, fora do Git. Confira seu tamanho e SHA-256 antes e depois do parsing.
2. Execute parse_demo sobre a demo concluída e grave stdout em data/parsed/, também fora do Git. Não substitua um JSON anterior sem revisar a entrada.
3. Valide a sintaxe com python3 -m json.tool e compare os campos efetivamente presentes.
4. Execute python3 scripts/analyze_demo.py sobre o JSON privado. O relatório individual vai para data/reports/ e não inclui chat, nomes ou SteamIDs.
5. Execute python3 -m unittest discover -s tests -v. Para a interface, execute npm test e npm run build.

Exemplo com uma demo sua, usando nomes substituíveis:

    /tmp/tf-demo-parser-install/bin/parse_demo data/demos/AAAA-MM-DD_HH-MM-SS.dem > data/parsed/AAAA-MM-DD_HH-MM-SS.json
    python3 -m json.tool data/parsed/AAAA-MM-DD_HH-MM-SS.json > /dev/null
    python3 scripts/analyze_demo.py data/parsed/AAAA-MM-DD_HH-MM-SS.json

## Schema observado no resumo padrão

| Campo raiz | Estrutura observada | Uso e limite |
|---|---|---|
| header | Objeto com nick, map, duration, ticks, frames, game, demo_type, version, protocol, server e signon | Nick e servidor são privados; duração e mapa são contexto da demo. |
| users | Objeto indexado por ID textual; cada usuário tem userId, name, steamId, team e classes | Identifica o jogador internamente, sem publicar identidades. A correspondência entre header.nick e users[].name precisa ser exata e única. |
| deaths | Lista com weapon, victim, assister opcional, killer e tick | Base das contagens individuais. O rótulo weapon não comprova arma equipada. |
| rounds | Lista com winner, length e end_tick | Contexto global, nunca estatística individual. |
| chat | Lista com kind, from, text e tick | Ignorada integralmente nos relatórios. |
| startTick | Inteiro | Só permite tempo relativo se compatível com os ticks dos eventos. |
| intervalPerTick | Número | Necessário com startTick para derivar segundos relativos. |
| pauses | Lista | Pode existir sem elementos; não presumir duração a subtrair. |

O resumo padrão observado não continha posições, trajetórias, mira, linha de visão, estado de sentries ou sequência temporal de mudanças de classe. A ausência desses campos no resumo não prova ausência na demo bruta. Uma demo POV não equivale ao estado completo do servidor.

O analisador separa fatos individuais de contexto global. Ele conta eliminações, mortes, assistências e autoeliminações apenas quando os IDs do jogador selecionado aparecem nos eventos relevantes. Se o POV não corresponder a uma identidade única, informe o SteamID ao comando por --steam-id; o identificador é usado internamente e não entra no Markdown. Fixtures de teste são pequenas e anonimizadas.
