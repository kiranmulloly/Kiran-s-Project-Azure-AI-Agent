## Module: session-hosts
## Lives in the shared terraform-avd-modules repo, consumed by every
## persona's deployment repo via a pinned git ref. Illustrative only.
##
## Contains the for_each loop that builds N session hosts from a
## locals-derived name list -- kept here, not in the deployment repo, so
## every persona gets the identical VM/NIC/extension shape and any future
## fix (e.g. a new extension version) ships to all 50 host pools by
## bumping one `ref`, not by hand-editing 50 copies of this file.

locals {
  host_indices = range(var.session_host_count)
  host_names   = [for i in local.host_indices : format("vm-%s-%02d", var.persona_name, i + 1)]
}

resource "azurerm_network_interface" "session_host" {
  for_each            = toset(local.host_names)
  name                = "nic-${each.value}"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Dynamic"
  }
}

resource "azurerm_windows_virtual_machine" "session_host" {
  for_each = toset(local.host_names)

  name                  = each.value
  resource_group_name   = var.resource_group_name
  location              = var.location
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
      hostPoolName = var.host_pool_name
    }
  })

  protected_settings = jsonencode({
    properties = {
      registrationInfoToken = var.registration_token
    }
  })
}
