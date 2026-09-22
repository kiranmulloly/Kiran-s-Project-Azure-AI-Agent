output "fslogix_private_endpoint_id" {
  value = azurerm_private_endpoint.fslogix_storage.id
}

output "avd_workspace_private_endpoint_id" {
  value = azurerm_private_endpoint.avd_workspace.id
}
