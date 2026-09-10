from django.conf import settings
from .models import School, SchoolDomain

ROOT_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
}

class TenantResolutionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.school = self.resolve_school(request)
        return self.get_response(request)

    def resolve_school(self, request):
        # Le header est accepté uniquement en développement.
        # En production, le hostname est la source de vérité.
        if settings.DEBUG:
            dev_slug = request.headers.get("X-Tenant-Slug")
            if dev_slug:
                return School.objects.filter(
                    slug=dev_slug,
                    status=School.Status.ACTIVE,
                ).first()

        host = request.get_host().split(":")[0].lower()

        if host in ROOT_HOSTS:
            return None

        # *.localhost
        if host.endswith(".localhost"):
            slug = host[:-len(".localhost")]
            if slug and "." not in slug:
                return School.objects.filter(
                    slug=slug,
                    status=School.Status.ACTIVE,
                ).first()

        # Wildcard du domaine principal.
        # Exemple: saint-joseph.prototype.bewiseinnovation.com
        base_domain = settings.BASE_DOMAIN.lower()
        suffix = f".{base_domain}"

        if host.endswith(suffix):
            slug = host[:-len(suffix)]
            if slug and "." not in slug:
                school = School.objects.filter(
                    slug=slug,
                    status=School.Status.ACTIVE,
                ).first()
                if school:
                    return school

        # Futurs domaines personnalisés.
        domain = SchoolDomain.objects.select_related("school").filter(
            domain=host,
            school__status=School.Status.ACTIVE,
        ).first()

        return domain.school if domain else None
