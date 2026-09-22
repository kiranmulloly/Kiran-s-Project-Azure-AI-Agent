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

variable "private_endpoint_subnet_id" {
  description = "From the networking module's output"
  type        = string
}

variable "workspace_id" {
  description = "From the workspace module's output"
  type        = string
}

variable "fslogix_storage_account_id" {
  description = "Resource ID of the (centrally-managed) FSLogix profile storage account"
  type        = string
}

variable "private_dns_zone_id_storage" {
  description = "Centrally-managed private DNS zone for privatelink.file.core.windows.net"
  type        = string
}

variable "private_dns_zone_id_avd" {
  description = "Centrally-managed private DNS zone for privatelink.wvd.microsoft.com"
  type        = string
}
