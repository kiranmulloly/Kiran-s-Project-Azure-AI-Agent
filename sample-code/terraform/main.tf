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
  description = "Compute Gallery image version ID (the 'golden image') session hosts are built from. Tagged onto each VM so the session-host-replacer can detect drift when a new version is published."
  type        = string
}

variable "registration_token" {
  description = "AVD host pool registration token used by the DSC extension to join each VM to the pool"
  type        = string
  sensitive   = true
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

# ---------------------------------------------------------------------------
# Session hosts: built with a `for` expression over a locals-derived name
# list rather than plain `count`, so each host gets a stable, human-readable
# name (vm-<persona>-01, -02, ...) that survives individual host replacement
# without renumbering the whole pool -- important once the session-host
# replacer starts swapping individual hosts out from under a live pool.
# ---------------------------------------------------------------------------

locals {
  host_indices = range(var.session_host_count)
  host_names   = [for i in local.host_indices : format("vm-%s-%02d", var.persona_name, i + 1)]
}

resource "azurerm_network_interface" "session_host" {
  for_each            = toset(local.host_names)
  name                = "nic-${each.value}"
  location            = azurerm_resource_group.avd.location
  resource_group_name = azurerm_resource_group.avd.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_windows_virtual_machine" "session_host" {
  for_each = toset(local.host_names)

  name                  = each.value
  resource_group_name   = azurerm_resource_group.avd.name
  location              = azurerm_resource_group.avd.location
  size                  = var.vm_sku
  admin_username        = var.admin_username
  admin_password        = var.admin_password
  network_interface_ids = [azurerm_network_interface.session_host[each.key].id]

  # Built from the golden image published to the Compute Gallery, not a
  # generic marketplace image -- keeps every host in the pool identical.
  source_image_id = var.image_version_id

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Premium_LRS"
  }

  tags = {
    persona       = var.persona_name
    role          = "avd-session-host"
    image_version = var.image_version_id
  }
}

# DSC extension joins each VM to the host pool using the registration token.
# Looping this over the same for_each map (rather than a separate count)
# keeps each extension bound to its specific VM even after individual hosts
# get replaced.
resource "azurerm_virtual_machine_extension" "avd_registration" {
  for_each = azurerm_windows_virtual_machine.session_host

  name                       = "avd-dsc-registration"
  virtual_machine_id         = each.value.id
  publisher                  = "Microsoft.Powershell"
  type                       = "DSC"
  type_handler_version       = "2.83"
  auto_upgrade_minor_version = true

  settings = jsonencode({
    modulesUrl            = "https://wvdportalstorageblob.blob.core.windows.net/galleryartifacts/Configuration.zip"
    configurationFunction = "Configuration.ps1\\AddSessionHost"
    properties = {
      hostPoolName = azurerm_virtual_desktop_host_pool.this.name
    }
  })

  protected_settings = jsonencode({
    properties = {
      registrationInfoToken = var.registration_token
    }
  })
}

output "host_pool_id" {
  value = azurerm_virtual_desktop_host_pool.this.id
}

output "session_host_names" {
  value = local.host_names
}
