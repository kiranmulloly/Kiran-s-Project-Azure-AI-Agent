## Root variables for the deployment repo. Values come from
## environments/<env>/<persona>.tfvars (see that folder + docs/02 for the
## nested-by-environment layout). Secrets (admin_username, admin_password,
## registration_token) are deliberately NOT given defaults here and are
## never set in a committed .tfvars file -- injected at apply-time from a
## secrets store / pipeline secret variables instead.

variable "persona_name" {
  description = "Logical name for this business-unit deployment"
  type        = string
}

variable "environment" {
  description = "Environment name: pilot | prod"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus2"
}

# --- Host pool -------------------------------------------------------------

variable "maximum_sessions_allowed" {
  type    = number
  default = 8
}

variable "start_vm_on_connect" {
  type    = bool
  default = true
}

variable "friendly_name" {
  description = "User-facing name shown in the AVD client feed"
  type        = string
}

# --- Networking --------------------------------------------------------------

variable "vnet_address_space" {
  type = list(string)
}

variable "session_host_subnet_prefix" {
  type = string
}

variable "private_endpoint_subnet_prefix" {
  type = string
}

# --- Session hosts -----------------------------------------------------------

variable "session_host_count" {
  type    = number
  default = 4
}

variable "vm_sku" {
  type    = string
  default = "Standard_D4s_v5"
}

variable "image_version_id" {
  description = "Compute Gallery image version ID (the 'golden image')"
  type        = string
}

variable "admin_username" {
  type      = string
  sensitive = true
}

variable "admin_password" {
  type      = string
  sensitive = true
}

variable "registration_token" {
  type      = string
  sensitive = true
}

# --- Private endpoints ---------------------------------------------------

variable "fslogix_storage_account_id" {
  description = "Resource ID of the centrally-managed FSLogix profile storage account"
  type        = string
}

variable "private_dns_zone_id_storage" {
  type = string
}

variable "private_dns_zone_id_avd" {
  type = string
}

# --- Scaling plan --------------------------------------------------------

variable "time_zone" {
  type    = string
  default = "Eastern Standard Time"
}

variable "weekdays_only" {
  type    = bool
  default = true
}

variable "ramp_up_start_time" {
  type    = string
  default = "07:00"
}

variable "ramp_up_minimum_hosts_percent" {
  type    = number
  default = 50
}

variable "ramp_up_capacity_threshold_percent" {
  type    = number
  default = 75
}

variable "peak_start_time" {
  type    = string
  default = "09:00"
}

variable "ramp_down_start_time" {
  type    = string
  default = "18:00"
}

variable "ramp_down_minimum_hosts_percent" {
  type    = number
  default = 10
}

variable "ramp_down_capacity_threshold_percent" {
  type    = number
  default = 50
}

variable "ramp_down_force_logoff_users" {
  type    = bool
  default = false
}

variable "ramp_down_wait_time_minutes" {
  type    = number
  default = 30
}

variable "off_peak_start_time" {
  type    = string
  default = "20:00"
}
