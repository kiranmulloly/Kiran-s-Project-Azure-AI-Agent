# Generic example: persona-driven variable definitions
# Illustrative only -- not derived from any proprietary source.

persona_name        = "example-persona"
location            = "eastus2"
session_host_count  = 6
vm_sku              = "Standard_D4s_v5"
subnet_id           = "/subscriptions/<sub-id>/resourceGroups/rg-networking/providers/Microsoft.Network/virtualNetworks/vnet-avd/subnets/snet-session-hosts"
image_version_id    = "/subscriptions/<sub-id>/resourceGroups/rg-gallery/providers/Microsoft.Compute/galleries/gallery_avd/images/golden-image/versions/1.4.0"

# admin_username / admin_password / registration_token are intentionally
# NOT set here -- in the real pipeline these are injected at apply-time from
# a secrets store (Key Vault / pipeline secret variables), never committed
# to source control, even in a private repo.

# In a real multi-persona setup, one .tfvars file like this exists per
# business unit, and a wrapper/module consumes it to keep every environment
# consistent while allowing per-persona sizing and placement decisions.
