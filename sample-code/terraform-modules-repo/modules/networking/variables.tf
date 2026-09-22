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

variable "vnet_address_space" {
  description = "CIDR block(s) for this persona's VNet"
  type        = list(string)
}

variable "session_host_subnet_prefix" {
  description = "CIDR for the session-host subnet"
  type        = string
}

variable "private_endpoint_subnet_prefix" {
  description = "CIDR for the private-endpoint subnet"
  type        = string
}
