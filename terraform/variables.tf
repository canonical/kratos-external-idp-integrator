# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

variable "model_name" {
  description = "The Juju model name"
  type        = string
}

variable "app_name" {
  description = "The Juju application name"
  type        = string
}

variable "config" {
  description = "The charm config"
  type        = optional(object({
      client_id : string
      client_secret : string
      issuer_url : optional(string)
      provider : string
      provider_id : string
      scope : optional(string, "profile email address phone")
      microsoft_tenant_id : optional(string)
      apple_team_id : optional(string)
      apple_private_key_id : optional(string)
      apple_private_key : optional(string)
      })
  default     = {}
}

variable "constraints" {
  description = "The constraints to be applied"
  type        = string
  default     = ""
}

variable "units" {
  description = "The number of units"
  type        = number
  default     = 1
}

variable "base" {
  description = "The charm base"
  type        = string
  default     = "ubuntu@22.04"
}

variable "channel" {
  description = "The charm channel"
  type        = string
  default     = "latest/edge"
}

variable "revision" {
  description = "The charm revision"
  type        = number
  nullable    = true
  default     = null
}
