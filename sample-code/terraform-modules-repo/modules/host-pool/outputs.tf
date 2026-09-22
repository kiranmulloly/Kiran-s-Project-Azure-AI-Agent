output "host_pool_id" {
  value = azurerm_virtual_desktop_host_pool.this.id
}

output "host_pool_name" {
  value = azurerm_virtual_desktop_host_pool.this.name
}

output "resource_group_name" {
  value = azurerm_resource_group.avd.name
}

output "location" {
  value = azurerm_resource_group.avd.location
}
