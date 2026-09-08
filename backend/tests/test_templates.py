import io
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.core.doc_generator import DocxGenerator
from app.models.analysis import Analysis
from app.models.document import Document
from app.models.template import Template


def _docx_bytes(parts: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, body in parts.items():
            archive.writestr(name, body)
    return buffer.getvalue()


def _document_xml(paragraphs: list[str]) -> str:
    body = "".join(f"<w:p>{p}</w:p>" for p in paragraphs)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}</w:body></w:document>"
    )


def _run(text: str) -> str:
    return f'<w:r><w:t xml:space="preserve">{text}</w:t></w:r>'


def _sample_docx() -> bytes:
    return _docx_bytes(
        {
            "[Content_Types].xml": "<Types/>",
            "word/document.xml": _document_xml(
                [
                    _run("Defesa - {{ summary }}"),
                    _run("Pedidos: ") + _run("{{ requests }}"),
                    _run("{% for law in laws %}")
                    + _run("{{ law }}; ")
                    + _run("{% endfor %}"),
                    _run("Cliente: {{ cliente }}"),
                ]
            ),
        }
    )


def _write_sample(path: Path) -> Path:
    path.write_bytes(_sample_docx())
    return path


def _make_analysis(db_session, make_user, *, email="c1-owner@example.com",
                   username="c1-owner"):
    user = make_user(email=email, username=username)
    document = Document(
        user_id=user.id,
        filename="c1.pdf",
        file_path="/tmp/c1.pdf",
        content_type="application/pdf",
        status="completed",
        uploaded_at=datetime.now(timezone.utc),
    )
    db_session.add(document)
    db_session.flush()
    analysis = Analysis(
        document_id=document.id,
        summary="Resumo C1",
        requests=["Pedido A"],
        laws=["CPC art. 1"],
        evidence="prova",
        defense_theses=["Tese 1"],
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return user, analysis


# --- discovery unit tests (no DB) ---


def test_discover_placeholders_rejoins_split_runs(temp_dir):
    docx_path = temp_dir / "split.docx"
    docx_path.write_bytes(
        _docx_bytes(
            {
                "[Content_Types].xml": "<Types/>",
                "word/document.xml": _document_xml(
                    [_run("{{ summa") + _run("ry }} e {{ cliente }}")]
                ),
            }
        )
    )
    assert DocxGenerator.discover_placeholders(str(docx_path)) == [
        "{{cliente}}",
        "{{summary}}",
    ]


def test_discover_placeholders_ignores_loop_vars_filters_and_keywords(temp_dir):
    docx_path = temp_dir / "loops.docx"
    docx_path.write_bytes(
        _docx_bytes(
            {
                "[Content_Types].xml": "<Types/>",
                "word/document.xml": _document_xml(
                    [
                        _run("{% for t in defense_theses %}{{ t }}; {% endfor %}"),
                        _run("{{ generatedDefenseStrategy | upper }}"),
                        _run("{% if summary is defined %}ok{% endif %}"),
                    ]
                ),
            }
        )
    )
    assert DocxGenerator.discover_placeholders(str(docx_path)) == [
        "{{defense_theses}}",
        "{{generatedDefenseStrategy}}",
        "{{summary}}",
    ]


def test_discover_placeholders_rejects_invalid_files(temp_dir):
    garbage = temp_dir / "garbage.docx"
    garbage.write_bytes(b"not a zip")
    with pytest.raises(ValueError):
        DocxGenerator.discover_placeholders(str(garbage))

    no_document = temp_dir / "nodoc.docx"
    no_document.write_bytes(_docx_bytes({"[Content_Types].xml": "<Types/>"}))
    with pytest.raises(ValueError):
        DocxGenerator.discover_placeholders(str(no_document))

    with pytest.raises(FileNotFoundError):
        DocxGenerator.discover_placeholders(str(temp_dir / "missing.docx"))

    wrong_suffix = temp_dir / "template.txt"
    wrong_suffix.write_bytes(b"{{ summary }}")
    with pytest.raises(ValueError):
        DocxGenerator.discover_placeholders(str(wrong_suffix))


def test_base_template_has_no_unsupported_placeholders():
    from app.api.routes import templates as templates_routes

    base = templates_routes.BASE_TEMPLATE_PATH
    placeholders = DocxGenerator.discover_placeholders(str(base))
    assert placeholders, "base template should reference context keys"
    assert DocxGenerator.unsupported_placeholders(placeholders) == []


# --- upload / list route tests ---


def test_upload_template_discovers_placeholders_and_persists(
    client, db_session, make_user, auth_headers_for, monkeypatch, temp_dir
):
    user = make_user(email="tpl-upload@example.com", username="tpl-upload")

    from app.api.routes import templates as templates_routes

    monkeypatch.setattr(templates_routes, "TEMPLATE_UPLOAD_DIR", str(temp_dir))

    response = client.post(
        "/api/v1/templates",
        headers=auth_headers_for(user),
        files={
            "file": (
                "defesa.docx",
                _sample_docx(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"name": "Minha defesa"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Minha defesa"
    assert payload["placeholders"] == [
        "{{cliente}}",
        "{{laws}}",
        "{{requests}}",
        "{{summary}}",
    ]
    assert payload["unsupportedPlaceholders"] == ["{{cliente}}"]

    stored = db_session.query(Template).filter(Template.id == payload["id"]).one()
    assert stored.user_id == user.id
    assert Path(stored.file_path).exists()


def test_upload_template_rejects_non_docx(client, make_user, auth_headers_for):
    user = make_user(email="tpl-reject@example.com", username="tpl-reject")
    response = client.post(
        "/api/v1/templates",
        headers=auth_headers_for(user),
        files={"file": ("notes.txt", b"not a docx", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_template_rejects_corrupt_docx(
    client, make_user, auth_headers_for, monkeypatch, temp_dir
):
    user = make_user(email="tpl-corrupt@example.com", username="tpl-corrupt")

    from app.api.routes import templates as templates_routes

    monkeypatch.setattr(templates_routes, "TEMPLATE_UPLOAD_DIR", str(temp_dir))

    response = client.post(
        "/api/v1/templates",
        headers=auth_headers_for(user),
        files={"file": ("broken.docx", b"garbage-bytes", "application/octet-stream")},
    )
    assert response.status_code == 400


def test_list_templates_returns_only_own_newest_first(
    client, db_session, make_user, auth_headers_for
):
    owner = make_user(email="tpl-list@example.com", username="tpl-list")
    other = make_user(email="tpl-list-other@example.com", username="tpl-list-other")
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            Template(
                user_id=owner.id, name="old", file_path="/tmp/old.docx",
                placeholders=["{{summary}}"], created_at=now - timedelta(minutes=5),
            ),
            Template(
                user_id=owner.id, name="new", file_path="/tmp/new.docx",
                placeholders=[], created_at=now,
            ),
            Template(
                user_id=other.id, name="foreign", file_path="/tmp/foreign.docx",
                placeholders=[],
            ),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/templates", headers=auth_headers_for(owner))
    assert response.status_code == 200
    payload = response.json()
    assert [item["name"] for item in payload] == ["new", "old"]


# --- generate-with-template tests ---


def test_generate_with_template_uses_uploaded_file(
    client, db_session, make_user, auth_headers_for, monkeypatch, temp_dir
):
    user, analysis = _make_analysis(db_session, make_user)
    template_file = _write_sample(temp_dir / "custom.docx")
    template = Template(
        user_id=user.id,
        name="custom",
        file_path=str(template_file),
        placeholders=["{{summary}}", "{{requests}}"],
    )
    db_session.add(template)
    db_session.commit()

    from app.api.routes import templates as templates_routes

    captured = {}
    monkeypatch.setattr(
        templates_routes.DocxGenerator,
        "generate_defense",
        staticmethod(
            lambda analysis_dict, template_path: captured.setdefault(
                "template_path", template_path
            )
            or str(temp_dir / "generated.docx")
        ),
    )
    (temp_dir / "generated.docx").write_bytes(b"docx-bytes")

    response = client.get(
        f"/api/v1/analysis/{analysis.id}/docx?template_id={template.id}",
        headers=auth_headers_for(user),
    )

    assert response.status_code == 200
    assert captured["template_path"] == str(template_file)


def test_generate_with_incompatible_template_returns_422_naming_offenders(
    client, db_session, make_user, auth_headers_for
):
    user, analysis = _make_analysis(
        db_session, make_user,
        email="c1-422@example.com", username="c1-422",
    )
    template = Template(
        user_id=user.id,
        name="bad",
        file_path="/tmp/bad.docx",
        placeholders=["{{summary}}", "{{cliente}}", "{{numero_processo}}"],
    )
    db_session.add(template)
    db_session.commit()

    response = client.get(
        f"/api/v1/analysis/{analysis.id}/docx?template_id={template.id}",
        headers=auth_headers_for(user),
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["unsupported_placeholders"] == [
        "{{cliente}}",
        "{{numero_processo}}",
    ]
    assert "summary" in detail["supported_keys"]


def test_generate_with_other_users_template_returns_404(
    client, db_session, make_user, auth_headers_for
):
    user, analysis = _make_analysis(
        db_session, make_user,
        email="c1-victim@example.com", username="c1-victim",
    )
    intruder = make_user(email="c1-intruder@example.com", username="c1-intruder")
    template = Template(
        user_id=intruder.id,
        name="private",
        file_path="/tmp/private.docx",
        placeholders=[],
    )
    db_session.add(template)
    db_session.commit()

    response = client.get(
        f"/api/v1/analysis/{analysis.id}/docx?template_id={template.id}",
        headers=auth_headers_for(user),
    )
    assert response.status_code == 404
