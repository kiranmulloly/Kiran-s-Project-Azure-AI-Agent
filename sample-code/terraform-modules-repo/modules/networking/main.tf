## Module: networking
## VNet + two subnets (session hosts, private endpoints) + a basic NSG on
## the session-host subnet. In many real setups this module -- or even
## the whole VNet -- is owned by a separate central-networking team/repo
## and merely referenced by ID here; it's included as its own module so
## this portfolio can show the full chain end-to-end.

resource "azurerm_virtual_network" "this" {
  name                = "vnet-avd-${var.persona_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.vnet_address_space
}

resource "azurerm_subnet" "session_hosts" {
  name                 = "snet-session-hosts"
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.this.name
  address_prefixes     = [var.session_host_subnet_prefix]
}

resource "azurerm_subnet" "private_endpoints" {
  name                                          = "snet-private-endpoints"
  resource_group_name                           = var.resource_group_name
  virtual_network_name                          = azurerm_virtual_network.this.name
  address_prefixes                              = [var.private_endpoint_subnet_prefix]
  private_endpoint_network_policies             = "Disabled"
}

resource "azurerm_network_security_group" "session_hosts" {
  name                = "nsg-session-hosts-${var.persona_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_subnet_network_security_group_association" "session_hosts" {
  subnet_id                 = azurerm_subnet.session_hosts.id
  network_security_group_id = azurerm_network_security_group.session_hosts.id
}
