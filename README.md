# Kratos External IDP Integrator

[![CharmHub Badge](https://charmhub.io/kratos-external-idp-integrator/badge.svg)](https://charmhub.io/kratos-external-idp-integrator)
[![Juju](https://img.shields.io/badge/Juju%20-3.0+-%23E95420)](https://github.com/juju/juju)
[![License](https://img.shields.io/github/license/canonical/kratos-external-idp-integrator?label=License)](https://github.com/canonical/kratos-external-idp-integrator/blob/main/LICENSE)

[![Continuous Integration Status](https://github.com/canonical/kratos-external-idp-integrator/actions/workflows/on_push.yaml/badge.svg?branch=main)](https://github.com/canonical/kratos-external-idp-integrator/actions?query=branch%3Amain)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196.svg)](https://conventionalcommits.org)

## Description

This charm is used to configure an Ory Kratos charm to use an external provider.

## Usage

### Client registration

Before deploying this charm you should register an oidc client with the provider
you wish to use. Instructions for registering a client for some well known
providers can be found below.
Instructions for a larger list of providers can be found at the Ory
Kratos [docs](https://www.ory.sh/docs/kratos/social-signin/overview).

Note that after registering a client you will need to provide a redirect_uri to
the provider. It can be fetched once the integrator charm is deployed.

#### Azure AD

Instructions for registering a client on Azure AD can be
found [here](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app).

#### Okta

Instructions for registering a client on Okta can be
found [here](https://developer.okta.com/docs/guides/find-your-app-credentials/main/).

### Deployment

For the `kratos-external-idp-integrator` charm to be operative you need to
deploy it, configure it and integrate with the kratos charm.:

```shell
juju deploy kratos-external-idp-integrator
juju config kratos-external-idp-integrator \
    client_id={client_id} \
    client_secret={client_secret} \
    provider={provider}
juju integrate kratos-external-idp-integrator kratos
```

Note that depending on the type of the provider different configurations may be
necessary.

### Getting the `redirect_uri`

After deploying, configuring and integrating the integrator charm, its status
will change to active. Now you can get the `redirect_uri` by running:

```shell
juju run {unit_name} get-redirect-uri --wait
```

### Disable the provider

To disable provider, i.e remove it from Kratos, run:

```shell
juju config kratos-external-idp-integrator enabled=false
```

### Enable the provider

To enable a provider that has been disabled, you need to run:

```shell
juju run kratos-external-idp-integrator enabled=true
```

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on
enhancements to this charm following best practice guidelines, and
[CONTRIBUTING.md](https://github.com/canonical/kratos-external-idp-integrator/blob/main/CONTRIBUTING.md)
for developer guidance.
