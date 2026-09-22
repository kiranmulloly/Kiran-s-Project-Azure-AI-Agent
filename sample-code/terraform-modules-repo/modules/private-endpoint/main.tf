## Module: private-endpoint
## Two private endpoints, both landing in the dedicated PE subnet:
##   1. FSLogix profile storage (Azure Files) -- keeps user profile
##      traffic off the public internet entirely.
##   2. The AVD workspace feed -- so the client feed/broker connection
##      never leaves the private network either.
## DNS zone IDs are passed in rather than created here because DNS zones
## are typically centrally owned/shared across every persona, not
## provisioned per-persona.

resource "azurerm_private_endpoint" "fslogix_storage" {
  name                = "pe-fslogix-${var.persona_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "psc-fslogix-${var.persona_name}"
    private_connection_resource_id = var.fslogix_storage_account_id
    subresource_names              = ["file"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-fslogix"
    private_dns_zone_ids = [var.private_dns_zone_id_storage]
  }
}

resource "azurerm_private_endpoint" "avd_workspace" {
  name                = "pe-avd-feed-${var.persona_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "psc-avd-feed-${var.persona_name}"
    private_connection_resource_id = var.workspace_id
    subresource_names              = ["global"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "dns-avd-feed"
    private_dns_zone_ids = [var.private_dns_zone_id_avd]
  }
}
