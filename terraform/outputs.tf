# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.

output "app_name" {
  description = "The Juju application name"
  value       = juju_application.kratos-external-idp.name
}

output "provides" {
  description = "The Juju integrations that the charm provides"
  value = {
    kratos-external-idp = "kratos-external-idp"
  }
}
