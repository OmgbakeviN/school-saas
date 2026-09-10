from pathlib import Path
import ast
import shutil
import sys

ROOT = Path(__file__).resolve().parent
if not (ROOT / "backend").exists():
    cwd = Path.cwd()
    if (cwd / "backend").exists():
        ROOT = cwd

PEOPLE_URLS = ROOT / "backend/apps/people/urls.py"
STEP_URLS = ROOT / "backend/apps/people/step_03_2_urls.py"
STEP_VIEWS = ROOT / "backend/apps/people/step_03_2_views.py"
STEP_SERVICES = ROOT / "backend/apps/people/step_03_2_services.py"
STEP_SERIALIZERS = ROOT / "backend/apps/people/step_03_2_serializers.py"
REQUIREMENTS = ROOT / "backend/requirements.txt"


def fail(message):
    print(f"[ERREUR] {message}")
    sys.exit(1)


def backup(path):
    backup_path = path.with_suffix(path.suffix + ".bak-export-routes")
    if path.exists() and not backup_path.exists():
        shutil.copy2(path, backup_path)


for path in (
    PEOPLE_URLS,
    STEP_URLS,
    STEP_VIEWS,
    STEP_SERVICES,
    STEP_SERIALIZERS,
    REQUIREMENTS,
):
    if not path.exists():
        fail(f"Fichier introuvable : {path}")

backup(PEOPLE_URLS)
backup(REQUIREMENTS)

# Ensure XLSX support is installed.
requirements = REQUIREMENTS.read_text(encoding="utf-8")
if "openpyxl" not in requirements.lower():
    if requirements and not requirements.endswith("\n"):
        requirements += "\n"
    requirements += "openpyxl>=3.1,<4.0\n"
    REQUIREMENTS.write_text(requirements, encoding="utf-8")

# Repair apps.people.urls.
text = PEOPLE_URLS.read_text(encoding="utf-8")

if "from django.urls import include, path" not in text:
    if "from django.urls import path" in text:
        text = text.replace(
            "from django.urls import path",
            "from django.urls import include, path",
            1,
        )
    elif "from django.urls import include, path" not in text:
        text = "from django.urls import include, path\n" + text

include_line = '    path("", include("apps.people.step_03_2_urls")),'

# Remove accidental duplicate forms first.
lines = [
    line
    for line in text.splitlines()
    if "apps.people.step_03_2_urls" not in line
]
text = "\n".join(lines) + "\n"

closing = text.rfind("\n]")
if closing == -1:
    fail("Impossible de trouver la fin de urlpatterns dans apps/people/urls.py.")

text = text[:closing] + "\n" + include_line + text[closing:]

try:
    ast.parse(text, filename=str(PEOPLE_URLS))
except SyntaxError as exc:
    fail(
        f"apps/people/urls.py invalide après réparation : "
        f"{exc.msg} ligne {exc.lineno}"
    )

PEOPLE_URLS.write_text(text, encoding="utf-8")

# Validate all STEP 03.2 Python files.
for path in (
    PEOPLE_URLS,
    STEP_URLS,
    STEP_VIEWS,
    STEP_SERVICES,
    STEP_SERIALIZERS,
):
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        fail(f"{path}: {exc.msg} ligne {exc.lineno}")

print("[OK] Routes STEP 03.2 reconnectées à /api/people/.")
print("[OK] Route export attendue : /api/people/bulk/export/students/")
print("[OK] Route export attendue : /api/people/bulk/export/teachers/")
print("[OK] Route export attendue : /api/people/bulk/export/guardians/")
print("[OK] Route export attendue : /api/people/bulk/export/enrollments/")
print("")
print("Installe/actualise les dépendances :")
print(r"  pip install -r backend\requirements.txt")
print("")
print("Puis vérifie :")
print(r"  cd backend")
print(r"  python manage.py check")
print(r"  python manage.py spectacular --validate --file openapi-schema.yml")
print("")
print("Relance ensuite le serveur Django.")
