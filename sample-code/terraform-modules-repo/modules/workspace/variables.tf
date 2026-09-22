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
  description = "From the host-pool module's output"
  type        = string
}

variable "host_pool_id" {
  description = "From the host-pool module's output"
  type        = string
}

variable "friendly_name" {
  description = "User-facing name shown in the AVD/Windows 365 client feed"
  type        = string
}
