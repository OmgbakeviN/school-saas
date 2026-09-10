from pathlib import Path
import ast
import shutil
import sys

ROOT = Path(__file__).resolve().parent
if not (ROOT / "backend").exists():
    cwd = Path.cwd()
    if (cwd / "backend").exists():
        ROOT = cwd

TARGETS = {
    ROOT / "backend/apps/tenants/views.py": [
        "from drf_spectacular.types import OpenApiTypes",
        "from drf_spectacular.utils import extend_schema",
    ],
    ROOT / "backend/apps/academics/views.py": [
        "from drf_spectacular.types import OpenApiTypes",
        "from drf_spectacular.utils import extend_schema",
    ],
    ROOT / "backend/apps/people/views.py": [
        "from drf_spectacular.types import OpenApiTypes",
        "from drf_spectacular.utils import extend_schema",
    ],
    ROOT / "backend/apps/core/views.py": [
        "from drf_spectacular.types import OpenApiTypes",
        "from drf_spectacular.utils import extend_schema",
    ],
    ROOT / "backend/apps/academics/serializers.py": [
        "from drf_spectacular.utils import extend_schema_field",
    ],
    ROOT / "backend/apps/people/serializers.py": [
        "from drf_spectacular.utils import extend_schema_field",
    ],
}

def backup(path):
    backup_path = path.with_suffix(path.suffix + ".bak-before-swagger-repair")
    if path.exists() and not backup_path.exists():
        shutil.copy2(path, backup_path)

def repair_file(path, required_imports):
    if not path.exists():
        print(f"[WARN] Introuvable : {path}")
        return

    backup(path)
    lines = path.read_text(encoding="utf-8").splitlines()

    cleaned = [
        line
        for line in lines
        if line.strip() not in required_imports
    ]

    insert_at = 0
    if cleaned and cleaned[0].startswith("#!"):
        insert_at = 1
    if (
        len(cleaned) > insert_at
        and "coding" in cleaned[insert_at]
        and cleaned[insert_at].lstrip().startswith("#")
    ):
        insert_at += 1

    repaired = cleaned[:insert_at] + required_imports + cleaned[insert_at:]
    text = "\n".join(repaired).rstrip() + "\n"

    try:
        ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        print(
            f"[ERREUR] {path}\n"
            f"  ligne {exc.lineno}: {exc.msg}"
        )
        sys.exit(1)

    path.write_text(text, encoding="utf-8")
    print(f"[OK] {path.relative_to(ROOT)}")

def fix_step_03_2_installer():
    path = ROOT / "apply_step_03_2.py"
    if not path.exists():
        return

    backup(path)
    text = path.read_text(encoding="utf-8")

    start = text.find("def ensure_line_after_imports(path, import_line):")
    end = text.find("\n\ndef add_decorator_to_function", start)

    if start == -1 or end == -1:
        print(
            "[WARN] apply_step_03_2.py trouvé, mais la fonction "
            "ensure_line_after_imports n'a pas la forme attendue."
        )
        return

    safe_impl = '''def ensure_line_after_imports(path, import_line):
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    lines = [
        line
        for line in lines
        if line.strip() != import_line
    ]

    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if (
        len(lines) > insert_at
        and "coding" in lines[insert_at]
        and lines[insert_at].lstrip().startswith("#")
    ):
        insert_at += 1

    lines.insert(insert_at, import_line)
    path.write_text("\\n".join(lines).rstrip() + "\\n", encoding="utf-8")
'''

    text = text[:start] + safe_impl + text[end:]

    try:
        ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        print(
            "[WARN] Impossible de mettre à jour apply_step_03_2.py : "
            f"{exc.msg} ligne {exc.lineno}"
        )
        return

    path.write_text(text, encoding="utf-8")
    print("[OK] apply_step_03_2.py sécurisé")

for target, imports in TARGETS.items():
    repair_file(target, imports)

fix_step_03_2_installer()

print("")
print("[OK] Réparation Swagger/STEP 03.2 terminée.")
print("")
print("Lance maintenant :")
print(r"  cd backend")
print(r"  python manage.py check")
print(r"  python manage.py spectacular --validate --file openapi-schema.yml")
print(r"  python manage.py runserver 0.0.0.0:8000")
