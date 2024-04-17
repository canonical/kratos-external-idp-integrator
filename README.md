# Kratos External IDP Integrator

[![CharmHub Badge](https://charmhub.io/kratos-external-idp-integrator/badge.svg)](https://charmhub.io/kratos-external-idp-integrator)

## Description

This charm is used to configure an Ory Kratos charm to use an external provider.

## Usage

### Client registration

Before deploying this charm you should register an oidc client with the provider you wish to use. Instructions for
registering a client for some well known providers can be found below. Instructions for a larger list of providers can be found at the
Ory Kratos [docs](https://www.ory.sh/docs/kratos/social-signin/overview).

Note that after registering a client you will need to provide a redirect_uri to the provider. It can be fetched
once the integrator charm is deployed.

#### Azure AD

Instructions for registering a client on Azure AD can be found [here](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app).

#### Okta

Instructions for registering a client on Okta can be found [here](https://developer.okta.com/docs/guides/find-your-app-credentials/main/).

### Deployment

For the `kratos-external-idp-integrator` charm to be operative you need to deploy it, configure it and relate to the kratos charm.:
```commandline
juju deploy kratos-external-provider-integrator
juju config kratos-external-provider-integrator \
    client_id={client_id} \
    client_secret={client_secret} \
    provider={provider}
juju relate kratos-external-provider-integrator kratos
```

Note that depending on the type of the provider different configurations may be necessary.

### Getting the redirect_uri

After deploying, configuring and relating the integrator charm, its status will change to active. Now you can get the redirect_uri by running:
```commandline
juju run {unit_name} get-redirect-uri --wait
```

### Disable the provider

To disable provider, i.e remove it from Kratos, run:
```commandline
juju run {unit_name} disable --wait
```

### Enable the provider

To enable a provider that has been disabled, you need to run:
```commandline
juju run {unit_name} enable --wait
```

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on enhancements to this
charm following best practice guidelines, and
[CONTRIBUTING.md](https://github.com/canonical/kratos-external-idp-integrator/blob/main/CONTRIBUTING.md) for developer
guidance.
