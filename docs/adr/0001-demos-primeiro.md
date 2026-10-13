# ADR-0001 · Demos primeiro, vídeo apenas se necessário

**Status:** aceito para MVP (13/10/2026).

**Contexto:** o analista deve reconstruir jogadas espacialmente, não apenas K/D; entretanto, usuário dispõe de aproximadamente 50 GiB livres e deseja buffer de cerca de 2 GiB, sessão de até 2h e custo mínimo.

**Decisão:** iniciar por `.dem` nativas do TF2 e validar tecnicamente cada campo antes de prometer análise tática. A fonte POV tem cobertura incompleta; não presumir visibilidade de sentry atrás de parede, todos os inimigos ou posição absoluta com precisão garantida. Processamento de imagem/vídeo entra apenas se uma lacuna concreta justificar custo e complexidade.

**Consequências:** MVP barato e testável. Requisitos avançados de linha de visão/contrafactuais dependem de testes reais e talvez de geometria de mapa ou renderização posterior.
