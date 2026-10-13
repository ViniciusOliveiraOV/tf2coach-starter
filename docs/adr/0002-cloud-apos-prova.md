# ADR-0002 · Infra de nuvem somente depois da prova de valor local

**Status:** aceito para primeira etapa (13/10/2026).

**Contexto:** objetivo educacional inclui Terraform/DevOps; produto ainda não validou parsing e dados; o usuário quer uma entrega de um dia sem overengineering.

**Decisão:** primeiro validação local `.dem` → JSON; depois relatório factual. Nuvem e Terraform reais entram quando upload/worker forem requisitos verificados. Exercício Terraform local em `infra/terraform/local` é separado e não provisiona recurso externo.

**Consequências:** menor custo e menos riscos; aprendizagem infra acontece numa etapa posterior, com IAM mínimo, armazenamento privado, orçamento e destruição verificada.
