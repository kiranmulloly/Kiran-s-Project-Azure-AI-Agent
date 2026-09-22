variable "persona_name" {
  description = "Logical name for this business-unit deployment"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus2"
}
