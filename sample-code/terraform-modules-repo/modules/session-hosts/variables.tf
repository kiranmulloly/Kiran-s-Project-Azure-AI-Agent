variable "persona_name" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "host_pool_name" {
  description = "Name of the host pool these session hosts register to (from the host-pool module's output)"
  type        = string
}

variable "session_host_count" {
  type    = number
  default = 4
}

variable "vm_sku" {
  type    = string
  default = "Standard_D4s_v5"
}

variable "subnet_id" {
  type = string
}

variable "admin_username" {
  type      = string
  sensitive = true
}

variable "admin_password" {
  type      = string
  sensitive = true
}

variable "image_version_id" {
  description = "Compute Gallery image version ID (the 'golden image')"
  type        = string
}

variable "registration_token" {
  type      = string
  sensitive = true
}
