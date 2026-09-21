# Generic example: persona-driven variable definitions
# Illustrative only — not derived from any proprietary source.

persona_name        = "example-persona"
location            = "eastus2"
session_host_count  = 6
vm_sku              = "Standard_D4s_v5"

# In a real multi-persona setup, one .tfvars file like this exists per
# business unit, and a wrapper/module consumes it to keep every environment
# consistent while allowing per-persona sizing and placement decisions.
