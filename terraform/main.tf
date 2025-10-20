/**
 * # Terraform Module for Kratos External IDP Integrator Operator
 *
 * This is a Terraform module facilitating the deployment of the
 * kratos-external-idp-integrator charm using the Juju Terraform provider.
 */

resource "juju_application" "kratos-external-idp" {
  name        = var.app_name
  trust       = true
  config      = var.config
  constraints = var.constraints
  units       = var.units

  charm {
    name     = "kratos-external-idp-integrator"
    base     = var.base
    channel  = var.channel
    revision = var.revision
  }
  model_uuid = var.model
}
