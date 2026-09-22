## Module: host-pool
## Lives in the shared terraform-avd-modules repo, consumed by every
## persona's deployment repo via a pinned git ref. Illustrative only.
##
## Scope is deliberately narrow: resource group + the host pool resource
## itself. Workspace/application-group live in the separate `workspace`
## module, and scaling behavior lives in the separate `scaling-plan`
## module -- splitting these out means a change to one (e.g. a new
## scaling schedule) never forces a re-plan of the others.

resource "azurerm_resource_group" "avd" {
  name     = "rg-avd-${var.persona_name}-${var.environment}"
  location = var.location
}

resource "azurerm_virtual_desktop_host_pool" "this" {
  name                             = "hp-${var.persona_name}-${var.environment}"
  location                         = azurerm_resource_group.avd.location
  resource_group_name              = azurerm_resource_group.avd.name
  type                             = "Pooled"
  load_balancer_type               = "BreadthFirst"
  maximum_sessions_allowed         = var.maximum_sessions_allowed
  start_vm_on_connect              = var.start_vm_on_connect
  validate_environment             = false

  tags = {
    persona     = var.persona_name
    environment = var.environment
  }
}
