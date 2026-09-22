## Module: workspace
## Workspace + application group + the association between them. Split
## out from the host-pool module so a workspace/app-group naming or
## friendly-name change never forces a re-plan of the host pool itself.

resource "azurerm_virtual_desktop_workspace" "this" {
  name                = "ws-${var.persona_name}-${var.environment}"
  friendly_name       = var.friendly_name
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_virtual_desktop_application_group" "this" {
  name                         = "dag-${var.persona_name}-${var.environment}"
  location                     = var.location
  resource_group_name          = var.resource_group_name
  type                         = "Desktop"
  host_pool_id                 = var.host_pool_id
  default_desktop_display_name = var.friendly_name
}

resource "azurerm_virtual_desktop_workspace_application_group_association" "this" {
  workspace_id         = azurerm_virtual_desktop_workspace.this.id
  application_group_id = azurerm_virtual_desktop_application_group.this.id
}
