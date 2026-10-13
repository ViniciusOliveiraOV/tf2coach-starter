# ADR-0003 · Evidências, contrafactuais e conhecimento externo

**Status:** aceito como direção de arquitetura, implementação futura.

**Contexto:** o analista precisa avaliar fatos e possibilidades, aprendizado longitudinal e conhecimento atualizado de jogadores experientes.

**Decisão:** resultados divididos em **fato extraído**, **inferência contextual** e **hipótese contrafactual**. O crawler deverá atualizar entre 10 e 30 fontes qualificadas com licença/proveniência. O conhecimento externo será recuperado sob demanda; não presumir que RAG evita todas as alucinações ou que recomendação popular é correta.

**Consequências:** rastreabilidade, avaliações futuras e custo controlável; exige testes e verificação de licenças. Não é pré-requisito para o primeiro JSON.
