const ROOT_HOSTS = new Set(["localhost", "127.0.0.1"]);

function currentPortSuffix() {
  return window.location.port ? `:${window.location.port}` : "";
}

export function buildTenantUrl(slug) {
  const protocol = window.location.protocol;
  const hostname = window.location.hostname.toLowerCase();

  if (ROOT_HOSTS.has(hostname)) {
    return `${protocol}//${slug}.localhost${currentPortSuffix()}`;
  }

  // La création d'une école se fait depuis le domaine racine actuel.
  // Le même code fonctionne donc sur n'importe quel domaine de déploiement.
  return `${protocol}//${slug}.${hostname}${currentPortSuffix()}`;
}

export function getLocalTenantSlug() {
  const hostname = window.location.hostname.toLowerCase();

  if (hostname.endsWith(".localhost")) {
    return hostname.slice(0, -".localhost".length);
  }

  return null;
}
