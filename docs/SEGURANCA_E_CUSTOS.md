# Segurança, privacidade, confiabilidade e custo desde o início

O usuário é único e o projeto é pessoal, mas a conexão com Steam, arquivos locais, códigos de terceiros e futura nuvem **não é uma exceção à segurança**.

## Antes de executar algo

- Launcher pode iniciar jogo, **não** rodar comandos como `sudo`, alterar configurações existentes ou mexer em arquivos Steam sem autorização. Testar via `--dry-run` primeiro.
- Qualquer download de parser externo exige conferir origem e licença e, no desenvolvimento guiado, pedir a aprovação prevista para mudanças de dependência.
- Nunca salvar IDs pessoais/nicks/voz/chat sem necessidade explícita. Dados de outros jogadores podem aparecer em demos; não compartilhar ou publicar material bruto.
- Não registrar tokens, chaves, URLs assinadas ou arquivos privados em logs. Arquivos `.env` e relatórios locais não devem entrar no Git.

## Política de armazenamento (a implementar, NÃO ativa)

- Meta de buffer: 2 GiB; aplicar proteção real **antes** de upload/gravação extensa, sem pressupor que heurística evita exceder o teto.
- Watcher reconhece arquivos fechados de forma robusta; `mtime` isolado é insuficiente.
- Upload com autenticação e destino privado; verificar checksum, tamanho e confirmação remota.
- Se falhar upload, preservar original e notificar. Se não houver espaço, interromper novas capturas de forma segura, não apagar o único exemplar.
- Aplicar retenção explícita **separada** para demo bruta e relatórios; exclusão local só após testes de recuperação e autorização.
- Uma partida pode ultrapassar 2 GiB; testar e comunicar impossibilidade de garantia rígida no sistema de gravação nativo.

## Cloud / Terraform (ainda não autorizado)

- Não criar conta/recursos cloud automaticamente. Antes, escolher provedor, região, serviços, estimativa mensal e limite aceitável.
- IAM com privilégio mínimo, bucket não público, criptografia em repouso e em trânsito, logs com retenção, evitar credenciais de longo prazo.
- OIDC para CI quando aplicável; não commitar `tfstate`, secretos nem dados pessoais. Estado remoto criptografado com locking e controle de acesso quando necessário.
- Configurar alertas de orçamento e guardrails. **Alertas não interrompem cobrança automaticamente**.
- Testar cenários: interrupção de rede, arquivo parcialmente escrito, falha de worker, reenvio duplicado, tamanho excessivo e rollback. Cotas de upload/tamanho, rate limiting se houver endpoint público.
- Nenhum deploy pago antes da aprovação explícita dos custos e do plano.

## Crawler futuro

- Entre 10 e 30 fontes; validar individualmente robots.txt, termos de acesso, licenças e frequência permitida; preferir APIs oficiais quando exigidas.
- Registrar URL, autor, data da coleta, data original, versão do jogo, tipo de partida, condições de uso e nível de evidência.
- Não transformar texto de fórum em norma tática; evitar fontes banidas, paywalls contornados, reuso sem licença e coleta massiva indevida.
- Atualização incremental, dedupe, controles de frequência, falhas e expiração de conhecimento antigo.

## Segurança de prompts

- Conteúdo crawleado não é instrução de sistema. Tratar como dado não confiável. Escapar e limitar conteúdo antes de alimentar o modelo.
- O LLM não deve executar operações de infraestrutura nem ter chaves de cloud disponíveis por padrão.
- Separar cálculo determinístico, raciocínio hipotético e narrativa; testar groundedness de recomendações.
