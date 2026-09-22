# Pilot environment -- example-persona
# Illustrative only -- not derived from any proprietary source.
# Almost every non-secret variable from ../../variables.tf is set
# explicitly here, even where it matches a module default, so the full
# effective config for this persona is visible in one file.

persona_name = "example-persona"
environment  = "pilot"
location     = "eastus2"
friendly_name = "Example Persona (Pilot)"

# --- Host pool ---------------------------------------------------------
maximum_sessions_allowed = 4
start_vm_on_connect      = true

# --- Networking ----------------------------------------------------------
vnet_address_space             = ["10.20.0.0/16"]
session_host_subnet_prefix     = "10.20.1.0/24"
private_endpoint_subnet_prefix = "10.20.2.0/24"

# --- Session hosts -------------------------------------------------------
session_host_count = 2
vm_sku             = "Standard_D4s_v5"
image_version_id   = "/subscriptions/<sub-id>/resourceGroups/rg-gallery/providers/Microsoft.Compute/galleries/gallery_avd/images/golden-image/versions/1.5.0-pilot"

# --- Private endpoints -----------------------------------------------------
fslogix_storage_account_id  = "/subscriptions/<sub-id>/resourceGroups/rg-storage-pilot/providers/Microsoft.Storage/storageAccounts/stfslogixpilot"
private_dns_zone_id_storage = "/subscriptions/<sub-id>/resourceGroups/rg-dns/providers/Microsoft.Network/privateDnsZones/privatelink.file.core.windows.net"
private_dns_zone_id_avd     = "/subscriptions/<sub-id>/resourceGroups/rg-dns/providers/Microsoft.Network/privateDnsZones/privatelink.wvd.microsoft.com"

# --- Scaling plan: shorter ramp windows, tighter ramp-down since pilot ---
# --- traffic is low and predictable, unlike prod                       ---
time_zone                            = "Eastern Standard Time"
weekdays_only                        = true
ramp_up_start_time                   = "07:30"
ramp_up_minimum_hosts_percent        = 50
ramp_up_capacity_threshold_percent   = 80
peak_start_time                      = "09:00"
ramp_down_start_time                 = "17:00"
ramp_down_minimum_hosts_percent      = 0
ramp_down_capacity_threshold_percent = 60
ramp_down_force_logoff_users         = true
ramp_down_wait_time_minutes          = 15
off_peak_start_time                  = "18:00"

# admin_username / admin_password / registration_token intentionally
# omitted -- injected at apply-time from the pipeline's secrets store.
