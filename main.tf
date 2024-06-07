# ---------------------------------------------------------------------------------------------------------------------
# ¦ VERSIONS
# ---------------------------------------------------------------------------------------------------------------------
terraform {
  required_version = ">= 1.3.10"

  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = ">= 4.47"
      configuration_aliases = []
    }
  }
}

provider "aws" {
  region  = "eu-central-1"
}

# ---------------------------------------------------------------------------------------------------------------------
# ¦ MODULE
# ---------------------------------------------------------------------------------------------------------------------
module "llm_backend" {
  source = "./modules/llm-backend"
}


data "aws_lambda_invocation" "llm_backend" {
  function_name = module.llm_backend.lambda_name

  input    = <<JSON
{
  "chat_query": "Give me all accounts in the Org Unit 'Production'."
}
JSON
}