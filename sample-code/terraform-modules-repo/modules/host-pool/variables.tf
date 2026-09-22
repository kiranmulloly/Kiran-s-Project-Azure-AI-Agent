variable "persona_name" {
  description = "Logical name for this business-unit deployment"
  type        = string
}

variable "environment" {
  description = "Environment name (pilot, prod, ...) -- used in resource naming/tags"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus2"
}

variable "maximum_sessions_allowed" {
  description = "Max concurrent user sessions per session host"
  type        = number
  default     = 8
}

variable "start_vm_on_connect" {
  description = "Whether Azure should power on a deallocated host when a user connects"
  type        = bool
  default     = true
}
