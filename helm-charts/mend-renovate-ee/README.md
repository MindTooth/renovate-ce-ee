# Mend Renovate Installation - Helm

## Add Helm repository

```shell
helm repo add mend-renovate-ce-ee https://mend.github.io/renovate-ce-ee
helm repo update
```

## Install Renovate chart

```shell
helm install --generate-name --set renovateWorker.config='\{\"token\":\"...\"\}' mend-renovate-ce-ee/mend-renovate-enterprise-edition
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
renovateWeb:
  enabled: true
route:
  enabled: true
  host: renovate-api.example.com
routeWeb:
  enabled: true
  host: renovate.example.com
```

Server and Web UI Routes are independent and can have separate hostnames. The Web
Route is rendered only when both `routeWeb.enabled` and `renovateWeb.enabled` are
true. Enabling the Web UI and its Route does not configure authentication.

**WARNING:** The Web UI provides administrative functionality. With
`renovateWeb.mendRnvPlatform: noauth`, anyone who can reach it can access it without
user authentication. Do not expose a Web UI using `noauth` to untrusted networks.
Configure appropriate authentication and restrict access before enabling its
Route. See [Web UI authentication](../../docs/web-ui.md).
