# operator-template

## Description

This charm is used to configure an Ory Kratos charm to use an external provider. It acts as a configuration charm.

## Usage

### Client registration

Before deploying this charm you should go and register an oidc client with the provider you wish to use. Instructions for
registering a client for some well known provider can be found below.

Note that after registering a client you will need to provide a redirect_uri to the provider, you will get the redirect_uri
after deploying the integrator.

#### Azure AD

Instructions for registering a client on Azure AD can be found [here](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app).

#### Okta

Instructions for registering a client on Azure AD can be found [here](https://developer.okta.com/docs/guides/find-your-app-credentials/main/).

### Deployment

For the kratos-external-idp-integrator charm to operate you need to deloy it, configure it and relate to a kratos charm.:
```commandline
juju deploy kratos-external-provider-integrator
juju config kratos-external-provider-integrator ...
juju relate kratos-external-provider-integrator kratos
```

### Getting the redirect_uri

After deploying, configuring and relating the integrator charm, its status will change to active. Now you can get the redirect_uri by running:
```commandline
juju run-action {unit_name} get-redirect-uri --wait
```

### Disable the provider

To disable provider, i.e remove it from Kratos, run:
```commandline
juju run-action {unit_name} disable --wait
```

### Enable the provider

To enable a provider that has been disabled, you need to run:
```commandline
juju run-action {unit_name} enable --wait
```

## Contributing

Please see the [Juju SDK docs](https://juju.is/docs/sdk) for guidelines on enhancements to this
charm following best practice guidelines, and
[CONTRIBUTING.md](https://github.com/canonical/kratos-external-idp-integrator/blob/main/CONTRIBUTING.md) for developer
guidance.
