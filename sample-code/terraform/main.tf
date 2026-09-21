## Generic example: AVD host pool + session hosts
## This is illustrative sample code for a portfolio project. It is not
## copied from any production/proprietary source and is not intended to
## be applied as-is against a real subscription without review.

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

resource "azurerm_resource_group" "avd" {
  name     = "rg-avd-${var.persona_name}"
  location = var.location
}

resource "azurerm_virtual_desktop_host_pool" "this" {
  name                = "hp-${var.persona_name}"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
  type                = "Pooled"
  load_balancer_type  = "BreadthFirst"
  validate_environment = false
}

resource "azurerm_virtual_desktop_workspace" "this" {
  name                = "ws-${var.persona_name}"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
}

resource "azurerm_virtual_desktop_application_group" "this" {
  name                = "dag-${var.persona_name}"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name
  type                = "Desktop"
  host_pool_id        = azurerm_virtual_desktop_host_pool.this.id
}

resource "azurerm_virtual_desktop_workspace_application_group_association" "this" {
  workspace_id         = azurerm_virtual_desktop_workspace.this.id
  application_group_id = azurerm_virtual_desktop_application_group.this.id
}

# Session host VMs would be provisioned here via azurerm_windows_virtual_machine
# (or a VM scale set), count = var.session_host_count, joined to the host pool
# via a registration-token-based DSC/script extension. Omitted here for
# brevity — see docs/02-terraform-provisioning-flow.md for the full narrative.

output "host_pool_id" {
  value = azurerm_virtual_desktop_host_pool.this.id
}
