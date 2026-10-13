# Terraform · exercício exclusivamente local

Esta configuração usa `terraform_data` e **não provisiona nada na nuvem**. Serve para aprender fluxo de plano/estado antes de recursos reais. O estado fica local e é ignorado pelo Git.

```bash
cd infra/terraform/local
terraform init
terraform plan
terraform apply  # apenas exercício LOCAL, se desejar
terraform destroy
```

Não confundir com infraestrutura de produção. O desenho futuro prevê storage privado, worker sob demanda, autenticação e logs mínimos; provedor/precificação só após o MVP ser validado e orçamento autorizado. Não usar Terraform para resolver um problema que ainda não existe.
