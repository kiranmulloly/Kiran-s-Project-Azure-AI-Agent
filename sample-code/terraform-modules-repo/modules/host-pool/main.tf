## Module: host-pool
## Lives in the shared terraform-avd-modules repo, consumed by every
## persona's deployment repo via a pinned git ref. Illustrative only.

resource "azurerm_resource_group" "avd" {
  name     = "rg-avd-${var.persona_name}"
  location = var.location
}

resource "azurerm_virtual_desktop_host_pool" "this" {
  name                 = "hp-${var.persona_name}"
  location             = azurerm_resource_group.avd.location
  resource_group_name  = azurerm_resource_group.avd.name
  type                 = "Pooled"
  load_balancer_type   = "BreadthFirst"
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
