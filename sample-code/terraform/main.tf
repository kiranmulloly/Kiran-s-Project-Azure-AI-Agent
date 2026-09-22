## Generic example: AVD persona deployment (the "deployment repo" side).
## This is illustrative sample code for a portfolio project. It is not
## copied from any production/proprietary source and is not intended to
## be applied as-is against a real subscription without review.
##
## Notice this file does NOT define host-pool/VM resources directly -- it
## calls versioned modules published from a SEPARATE repository
## (see ../terraform-modules-repo/). Every one of the 50 persona deployment
## repos in the real platform looks like this: thin, mostly just wiring
## together shared modules with per-persona variable values. All the actual
## resource logic lives in one place and ships to every consumer by version
## bump, not by copy-paste.

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "persona_name" {
  description = "Logical name for this business-unit deployment"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus2"
}

variable "session_host_count" {
  description = "Desired number of session hosts in the pool"
  type        = number
  default     = 4
}

variable "vm_sku" {
  description = "VM size for session hosts"
  type        = string
  default     = "Standard_D4s_v5"
}

variable "subnet_id" {
  description = "Subnet to attach session host NICs to"
  type        = string
}

variable "admin_username" {
  type      = string
  sensitive = true
}

variable "admin_password" {
  type      = string
  sensitive = true
}

variable "image_version_id" {
  description = "Compute Gallery image version ID (the 'golden image')"
  type        = string
}

variable "registration_token" {
  description = "AVD host pool registration token"
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# Modules pulled from a SEPARATE repository (terraform-avd-modules), pinned
# to an explicit release tag. Bumping `ref` here is the only way this
# environment's resource shape ever changes -- nothing auto-upgrades.
# See sample-code/terraform-modules-repo/README.md for the versioning
# strategy and layout of the module source repo.
# ---------------------------------------------------------------------------

module "host_pool" {
  source = "git::https://github.com/example-org/terraform-avd-modules.git//modules/host-pool?ref=v1.4.0"

  persona_name = var.persona_name
  location     = var.location
}

module "session_hosts" {
  source = "git::https://github.com/example-org/terraform-avd-modules.git//modules/session-hosts?ref=v1.4.0"

  persona_name        = var.persona_name
  location            = var.location
  resource_group_name = module.host_pool.resource_group_name
  host_pool_name      = module.host_pool.host_pool_name

  session_host_count = var.session_host_count
  vm_sku             = var.vm_sku
  subnet_id          = var.subnet_id
  admin_username     = var.admin_username
  admin_password     = var.admin_password
  image_version_id   = var.image_version_id
  registration_token = var.registration_token
}

output "host_pool_id" {
  value = module.host_pool.host_pool_id
}

output "session_host_names" {
  value = module.session_hosts.session_host_names
}
