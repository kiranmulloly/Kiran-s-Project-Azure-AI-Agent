output "session_host_names" {
  value = local.host_names
}

output "session_host_ids" {
  value = { for name, vm in azurerm_windows_virtual_machine.session_host : name => vm.id }
}
