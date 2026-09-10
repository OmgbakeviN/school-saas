TENANT_HEADER = {
    "name": "X-Tenant-Slug",
    "in": "header",
    "required": False,
    "description": (
        "Développement local uniquement. Slug de l'établissement, par exemple "
        "`saint-joseph`. En production, le tenant est normalement résolu depuis "
        "le sous-domaine."
    ),
    "schema": {"type": "string", "example": "saint-joseph"},
}

SKIP_PREFIXES = (
    "/api/public/",
    "/api/schema/",
    "/api/docs/",
    "/api/redoc/",
)

SKIP_EXACT = {
    "/api/auth/login/",
    "/api/auth/refresh/",
}

def add_tenant_header_parameter(result, generator, request, public):
    # Ajoute X-Tenant-Slug aux opérations tenant du schéma.
    for path, path_item in result.get("paths", {}).items():
        if path in SKIP_EXACT or path.startswith(SKIP_PREFIXES):
            continue
        for method in ("get", "post", "put", "patch", "delete"):
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            parameters = operation.setdefault("parameters", [])
            if not any(
                isinstance(parameter, dict)
                and parameter.get("name") == "X-Tenant-Slug"
                and parameter.get("in") == "header"
                for parameter in parameters
            ):
                parameters.append(dict(TENANT_HEADER))
    return result
