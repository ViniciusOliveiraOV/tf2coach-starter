# Exercício deliberadamente local para conhecer init/plan/apply/destroy.
# Recurso terraform_data não acessa provedores/cloud.
terraform {
  required_version = ">= 1.5.0"
}

variable "project_name" {
  type        = string
  description = "Identificador local do laboratório"
  default     = "tf2coach"
}

resource "terraform_data" "sandbox" {
  input = {
    project     = var.project_name
    environment = "local-only"
  }
}

output "sandbox" {
  description = "Saída meramente local do exemplo"
  value       = terraform_data.sandbox.output
}
