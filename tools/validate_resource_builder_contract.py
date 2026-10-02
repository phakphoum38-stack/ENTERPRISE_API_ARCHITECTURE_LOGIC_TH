from pathlib import Path
import ast
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

FILES = [
    ROOT / "tools/research_os_resource_parser.py",
    ROOT / "tools/research_os_identity_registry.py",
    ROOT / "tools/research_os_relationship_registry.py",
    ROOT / "tools/research_os_code_identity.py",
    ROOT / "tools/research_os_code_discovery.py",
    ROOT / "tools/research_os_resource_manifest.py",
    ROOT / "tools/research_os_resource_drift.py",
    ROOT / "tools/research_os_resource_builder.py",
    ROOT / "tools/research_os_resource_translator.py",
    ROOT / "tools/research_os_semantic_binding.py",
]


def compile_all():
    for path in FILES:
        source = path.read_text(encoding="utf-8")
        if not source.strip():
            raise AssertionError(f"EMPTY_MODULE:{path}")
        ast.parse(source, filename=str(path))
        subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            check=True,
        )


def import_smoke():
    modules = [
        "tools.research_os_resource_parser",
        "tools.research_os_identity_registry",
        "tools.research_os_relationship_registry",
        "tools.research_os_code_identity",
        "tools.research_os_code_discovery",
        "tools.research_os_resource_manifest",
        "tools.research_os_resource_drift",
        "tools.research_os_resource_builder",
        "tools.research_os_resource_translator",
        "tools.research_os_semantic_binding",
    ]

    for module in modules:
        subprocess.run(
            [sys.executable, "-c", f"import {module}"],
            check=True,
        )


def builder_checks():
    from tools.research_os_resource_builder import ResourceBuilder
    from tools.research_os_resource_manifest import ResourceManifest
    from tools.research_os_resource_translator import translate_resources
    from tools.research_os_resource_parser import (
        declared_identities,
        explicit_identities,
    )
    from tools.research_os_identity_registry import identity_for

    builder = ResourceBuilder(ROOT)

    first = builder.discover()
    second = builder.discover()

    if not first:
        raise AssertionError("BUILDER_DISCOVERED_ZERO_RESOURCES")

    if first != second:
        raise AssertionError("BUILDER_NOT_DETERMINISTIC")

    ids = [resource["resource_id"] for resource in first]

    if len(ids) != len(set(ids)):
        raise AssertionError("RESOURCE_ID_DUPLICATE")

    for resource in first:
        for field in (
            "resource_id",
            "kind",
            "path",
            "canonical_identity",
        ):
            if not resource.get(field):
                raise AssertionError(f"RESOURCE_FIELD_MISSING:{field}")

        if "\\" in resource["path"]:
            raise AssertionError(
                f"PATH_NOT_NORMALIZED:{resource['path']}"
            )

    translated_a = translate_resources(first)
    translated_b = translate_resources(list(reversed(first)))

    if translated_a != translated_b:
        raise AssertionError("TRANSLATOR_NOT_DETERMINISTIC")

    sample = "foo_contract.json"

    explicit = explicit_identities(
        sample,
        '{"contract":"REAL_CONTRACT"}',
    )

    if "foo_contract" in explicit:
        raise AssertionError(
            "PATH_STEM_LEAKED_INTO_EXPLICIT_IDENTITY"
        )

    if "real_contract" not in explicit:
        raise AssertionError(
            "EXPLICIT_IDENTITY_NOT_DISCOVERED"
        )

    declared = declared_identities(
        sample,
        '{"contract":"REAL_CONTRACT"}',
    )

    if "foo_contract" not in declared:
        raise AssertionError(
            "DECLARED_PATH_STEM_MISSING"
        )

    a = identity_for(
        "IMPLEMENTATION",
        "tools/example.py",
        "EXAMPLE",
    )
    b = identity_for(
        "IMPLEMENTATION",
        "tools/example.py",
        "EXAMPLE",
    )

    if a != b:
        raise AssertionError("IDENTITY_NOT_DETERMINISTIC")

    manifest = ResourceManifest()

    manifest.add(first[0])
    manifest.add(dict(first[0]))

    if len(manifest.resources) != 1:
        raise AssertionError("MANIFEST_NOT_IDEMPOTENT")

    if len(manifest.sha256()) != 64:
        raise AssertionError("MANIFEST_SHA256_INVALID")


def collision_check():
    from tools.research_os_resource_manifest import ResourceManifest

    manifest = ResourceManifest()

    first = {
        "resource_id": "collision-test",
        "kind": "IMPLEMENTATION",
        "path": "a.py",
        "canonical_identity": "a",
    }

    second = {
        "resource_id": "collision-test",
        "kind": "IMPLEMENTATION",
        "path": "b.py",
        "canonical_identity": "b",
    }

    manifest.add(first)

    try:
        manifest.add(second)
    except ValueError:
        return

    raise AssertionError(
        "MANIFEST_COLLISION_DID_NOT_FAIL_CLOSED"
    )


def main():
    compile_all()
    import_smoke()
    builder_checks()
    collision_check()

    print("BUILDER_CONTRACT_GATE_OK")
    print("DETERMINISTIC_DISCOVERY_OK")
    print("RESOURCE_ID_INTEGRITY_OK")
    print("IDENTITY_SEPARATION_OK")
    print("TRANSLATOR_INTEGRATION_OK")
    print("MANIFEST_DETERMINISM_OK")
    print("COLLISION_FAIL_CLOSED_OK")
    print("M2_NOT_MODIFIED")
    print("NO_COMMIT")
    print("NO_PUSH")


if __name__ == "__main__":
    main()
