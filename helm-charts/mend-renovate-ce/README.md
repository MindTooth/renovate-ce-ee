# Mend Renovate Installation - Helm

## Add Helm repository

```shell
helm repo add mend-renovate-ce-ee https://mend.github.io/renovate-ce-ee
helm repo update
```

## Install Renovate chart

```shell
helm install --generate-name --set renovate.config='\{\"token\":\"...\"\}' mend-renovate-ce-ee/mend-renovate-ce
```

See [Configuration Options](https://github.com/mend/renovate-ce-ee/blob/main/docs/configuration-options.md) for more information.

## OpenShift Routes

Routes are optional and disabled by default. Route and Ingress are configured
independently; enabling a Route does not disable Ingress. Leave `host` empty to
let OpenShift generate a hostname. Annotations and the named Service `targetPort`
can be customized on each Route (default: `http`).

Edge TLS terminates HTTPS at the OpenShift router and uses HTTP to the application
backend; application HTTPS is not required. Only edge termination is supported.
Set `tls: null` for an HTTP-only Route; passthrough and re-encrypt are not supported.

```yaml
ingress:
  enabled: false
route:
  enabled: true
  host: renovate.example.com
  tls:
    termination: edge
    insecureEdgeTerminationPolicy: Redirect
```
