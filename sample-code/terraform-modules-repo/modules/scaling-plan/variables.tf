variable "persona_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "host_pool_id" {
  description = "From the host-pool module's output"
  type        = string
}

variable "time_zone" {
  type    = string
  default = "Eastern Standard Time"
}

variable "weekdays_only" {
  description = "If true, schedule only applies Mon-Fri; otherwise every day"
  type        = bool
  default     = true
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
