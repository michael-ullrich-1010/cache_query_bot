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

# ---------------------------------------------------------------------------------------------------------------------
# ¦ DATA
# ---------------------------------------------------------------------------------------------------------------------
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ---------------------------------------------------------------------------------------------------------------------
# ¦ LOCALS
# ---------------------------------------------------------------------------------------------------------------------
locals {
  resource_tags = var.resource_tags
}


# ---------------------------------------------------------------------------------------------------------------------
# ¦ MODULE
# ---------------------------------------------------------------------------------------------------------------------
#tfsec:ignore:AVD-AWS-0066
module "llm_backend" {
  #checkov:skip=CKV_TF_1: Currently version-tags are used
  #checkov:skip=CKV_AWS_50
  source  = "acai-consulting/lambda/aws"
  version = "1.3.4"

  lambda_settings = {
    function_name = var.settings.lambda_name
    description   = "Create a context cache query with the help of a LLM."
    layer_arn_list = [
      replace(var.lambda_settings.layer_arns["aws_lambda_powertools_python_layer_arn"], "$region", data.aws_region.current.name),
    ]
    config  = var.lambda_settings
    error_handling = var.lambda_settings.error_forwarder == null ? null : {
      central_collector = var.lambda_settings.error_forwarder
    }
    handler = "main.lambda_handler"
    package = {
      source_path = "${path.module}/lambda-files"
    }
    tracing_mode = var.lambda_settings.tracing_mode
    environment_variables = {
      LOG_LEVEL                = var.lambda_settings.log_level
      BEDROCK_SERVICE_NAME      = var.settings.bedrock_service_name
      BEDROCK_SERVICE_REGION      = var.settings.bedrock_service_region
      BEDROCK_MODEL_ID      = var.settings.bedrock_model_id
    }
  }
  resource_tags = local.resource_tags
}


# ---------------------------------------------------------------------------------------------------------------------
# ¦ ASSIGN CACHE POLICY TO LAMBDA EXECUTION ROLE
# ---------------------------------------------------------------------------------------------------------------------
resource "aws_iam_role_policy" "process_user_prompt" {
  name   = replace(module.llm_backend.execution_iam_role.name, "role", "policy")
  role   = module.llm_backend.execution_iam_role.name
  policy = data.aws_iam_policy_document.lambda_permissions.json
}

#tfsec:ignore:AVD-AWS-0057
data "aws_iam_policy_document" "lambda_permissions" {
  statement {
    sid    = "ReadDataFromBedrock"
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
    ]
    resources = ["*"]
  }
}
