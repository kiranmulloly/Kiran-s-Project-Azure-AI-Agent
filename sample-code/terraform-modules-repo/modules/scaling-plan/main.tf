## Module: scaling-plan
## Ramp-up / peak / ramp-down / off-peak schedule + association to the
## host pool. This is what lets a pool shrink outside business hours
## instead of running 50 host pools' worth of VMs 24/7.

resource "azurerm_virtual_desktop_scaling_plan" "this" {
  name                = "sp-${var.persona_name}-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  friendly_name       = "Scaling plan for ${var.persona_name} (${var.environment})"
  time_zone           = var.time_zone

  schedule {
    name                                 = "weekday-schedule"
    days_of_week                         = var.weekdays_only ? ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] : ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    ramp_up_start_time                   = var.ramp_up_start_time
    ramp_up_load_balancing_algorithm     = "BreadthFirst"
    ramp_up_minimum_hosts_percent        = var.ramp_up_minimum_hosts_percent
    ramp_up_capacity_threshold_percent   = var.ramp_up_capacity_threshold_percent

    peak_start_time                      = var.peak_start_time
    peak_load_balancing_algorithm        = "DepthFirst"

    ramp_down_start_time                 = var.ramp_down_start_time
    ramp_down_load_balancing_algorithm   = "DepthFirst"
    ramp_down_minimum_hosts_percent      = var.ramp_down_minimum_hosts_percent
    ramp_down_capacity_threshold_percent = var.ramp_down_capacity_threshold_percent
    ramp_down_force_logoff_users         = var.ramp_down_force_logoff_users
    ramp_down_wait_time_minutes          = var.ramp_down_wait_time_minutes
    ramp_down_notification_message       = "This session will end in ${var.ramp_down_wait_time_minutes} minutes as part of scheduled off-peak scale-down. Please save your work."

    off_peak_start_time                  = var.off_peak_start_time
    off_peak_load_balancing_algorithm    = "DepthFirst"
  }

  host_pool {
    hostpool_id          = var.host_pool_id
    scaling_plan_enabled = true
  }
}
