## Generic example: AVD persona deployment (the "deployment repo" side).
## This is illustrative sample code for a portfolio project. It is not
## copied from any production/proprietary source and is not intended to
## be applied as-is against a real subscription without review.
##
## This file wires together every module published from the separate
## terraform-avd-modules repo (see ../terraform-modules-repo/): networking,
## host-pool, workspace, session-hosts, private-endpoint, and scaling-plan.
## All 50 persona deployment repos in the real platform look like this --
## thin, mostly just wiring shared modules together with per-persona
## variable values. Variable values themselves live in
## environments/<env>/<persona>.tfvars (see that folder for the nested
## per-environment, per-persona layout and docs/07 for why modules are
## versioned separately from this repo).

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

locals {
  module_ref = "v1.4.0" # pinned module-repo release; bump deliberately, never floats
  module_src = "git::https://github.com/example-org/terraform-avd-modules.git"
}

# ---------------------------------------------------------------------------
# Networking: VNet + session-host subnet + private-endpoint subnet + NSG
# ---------------------------------------------------------------------------
module "networking" {
  source = "${local.module_src}//modules/networking?ref=${local.module_ref}"

  persona_name                   = var.persona_name
  environment                    = var.environment
  location                       = var.location
  resource_group_name            = module.host_pool.resource_group_name
  vnet_address_space             = var.vnet_address_space
  session_host_subnet_prefix     = var.session_host_subnet_prefix
  private_endpoint_subnet_prefix = var.private_endpoint_subnet_prefix
}

# ---------------------------------------------------------------------------
# Host pool: resource group + the pool itself
# ---------------------------------------------------------------------------
module "host_pool" {
  source = "${local.module_src}//modules/host-pool?ref=${local.module_ref}"

  persona_name             = var.persona_name
  environment              = var.environment
  location                 = var.location
  maximum_sessions_allowed = var.maximum_sessions_allowed
  start_vm_on_connect      = var.start_vm_on_connect
}

# ---------------------------------------------------------------------------
# Workspace + application group, feeding off the host pool above
# ---------------------------------------------------------------------------
module "workspace" {
  source = "${local.module_src}//modules/workspace?ref=${local.module_ref}"

  persona_name         = var.persona_name
  environment          = var.environment
  location             = var.location
  resource_group_name  = module.host_pool.resource_group_name
  host_pool_id         = module.host_pool.host_pool_id
  friendly_name        = var.friendly_name
}

# ---------------------------------------------------------------------------
# Session hosts (VMs): the for_each loop building N hosts from the pinned
# golden image, landing in the networking module's session-host subnet
# ---------------------------------------------------------------------------
module "session_hosts" {
  source = "${local.module_src}//modules/session-hosts?ref=${local.module_ref}"

  persona_name        = var.persona_name
  location            = var.location
  resource_group_name = module.host_pool.resource_group_name
  host_pool_name      = module.host_pool.host_pool_name

  session_host_count = var.session_host_count
  vm_sku             = var.vm_sku
  subnet_id          = module.networking.session_host_subnet_id
  admin_username     = var.admin_username
  admin_password     = var.admin_password
  image_version_id   = var.image_version_id
  registration_token = var.registration_token
}

# ---------------------------------------------------------------------------
# Private endpoints: FSLogix storage + AVD workspace feed, both landing in
# the networking module's dedicated PE subnet
# ---------------------------------------------------------------------------
module "private_endpoint" {
  source = "${local.module_src}//modules/private-endpoint?ref=${local.module_ref}"

  persona_name                = var.persona_name
  environment                 = var.environment
  location                    = var.location
  resource_group_name         = module.host_pool.resource_group_name
  private_endpoint_subnet_id  = module.networking.private_endpoint_subnet_id
  workspace_id                = module.workspace.workspace_id
  fslogix_storage_account_id  = var.fslogix_storage_account_id
  private_dns_zone_id_storage = var.private_dns_zone_id_storage
  private_dns_zone_id_avd     = var.private_dns_zone_id_avd
}

# ---------------------------------------------------------------------------
# Scaling plan: ramp-up/peak/ramp-down/off-peak schedule tied to the pool
# ---------------------------------------------------------------------------
module "scaling_plan" {
  source = "${local.module_src}//modules/scaling-plan?ref=${local.module_ref}"

  persona_name         = var.persona_name
  environment          = var.environment
  location             = var.location
  resource_group_name  = module.host_pool.resource_group_name
  host_pool_id         = module.host_pool.host_pool_id

  time_zone                             = var.time_zone
  weekdays_only                         = var.weekdays_only
  ramp_up_start_time                    = var.ramp_up_start_time
  ramp_up_minimum_hosts_percent         = var.ramp_up_minimum_hosts_percent
  ramp_up_capacity_threshold_percent    = var.ramp_up_capacity_threshold_percent
  peak_start_time                       = var.peak_start_time
  ramp_down_start_time                  = var.ramp_down_start_time
  ramp_down_minimum_hosts_percent       = var.ramp_down_minimum_hosts_percent
  ramp_down_capacity_threshold_percent  = var.ramp_down_capacity_threshold_percent
  ramp_down_force_logoff_users          = var.ramp_down_force_logoff_users
  ramp_down_wait_time_minutes           = var.ramp_down_wait_time_minutes
  off_peak_start_time                   = var.off_peak_start_time
}

output "host_pool_id" {
  value = module.host_pool.host_pool_id
}

output "workspace_id" {
  value = module.workspace.workspace_id
}

output "session_host_names" {
  value = module.session_hosts.session_host_names
}

output "scaling_plan_id" {
  value = module.scaling_plan.scaling_plan_id
}
