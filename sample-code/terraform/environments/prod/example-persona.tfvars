# Production environment -- example-persona
# Illustrative only -- not derived from any proprietary source.
# Mirrors pilot/example-persona.tfvars variable-for-variable -- only the
# values differ. That symmetry is what makes pilot a meaningful baseline
# for this persona's production changes (see docs/01).

persona_name  = "example-persona"
environment   = "prod"
location      = "eastus2"
friendly_name = "Example Persona"

# --- Host pool ---------------------------------------------------------
maximum_sessions_allowed = 8
start_vm_on_connect      = true

# --- Networking ----------------------------------------------------------
vnet_address_space             = ["10.40.0.0/16"]
session_host_subnet_prefix     = "10.40.1.0/24"
private_endpoint_subnet_prefix = "10.40.2.0/24"

# --- Session hosts -------------------------------------------------------
session_host_count = 10
vm_sku             = "Standard_D4s_v5"
image_version_id   = "/subscriptions/<sub-id>/resourceGroups/rg-gallery/providers/Microsoft.Compute/galleries/gallery_avd/images/golden-image/versions/1.4.0"

# --- Private endpoints -----------------------------------------------------
fslogix_storage_account_id  = "/subscriptions/<sub-id>/resourceGroups/rg-storage-prod/providers/Microsoft.Storage/storageAccounts/stfslogixprod"
private_dns_zone_id_storage = "/subscriptions/<sub-id>/resourceGroups/rg-dns/providers/Microsoft.Network/privateDnsZones/privatelink.file.core.windows.net"
private_dns_zone_id_avd     = "/subscriptions/<sub-id>/resourceGroups/rg-dns/providers/Microsoft.Network/privateDnsZones/privatelink.wvd.microsoft.com"

# --- Scaling plan: longer peak window, gentler ramp-down, no forced ------
# --- logoff -- prod sessions run longer and unpredictably              ---
time_zone                            = "Eastern Standard Time"
weekdays_only                        = false
ramp_up_start_time                   = "06:00"
ramp_up_minimum_hosts_percent        = 60
ramp_up_capacity_threshold_percent   = 75
peak_start_time                      = "08:00"
ramp_down_start_time                 = "19:00"
ramp_down_minimum_hosts_percent      = 20
ramp_down_capacity_threshold_percent = 50
ramp_down_force_logoff_users         = false
ramp_down_wait_time_minutes          = 30
off_peak_start_time                  = "21:00"

# admin_username / admin_password / registration_token intentionally
# omitted -- injected at apply-time from the pipeline's secrets store,
# even in production.
