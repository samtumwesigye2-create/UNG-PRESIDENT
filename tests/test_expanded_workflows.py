import contextlib
import io
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ung_president as app


@pytest.fixture
def client(tmp_path):
    app.DB_PATH = str(tmp_path / "expanded-workflows.db")
    app._rate_buckets.clear()
    app.init_db()
    import registration_response_fix
    registration_response_fix.apply_registration_response_fix()
    import president_expanded_admin
    president_expanded_admin.apply_expanded_admin()
    with contextlib.redirect_stdout(io.StringIO()):
        with TestClient(app.app) as c:
            yield c


def login(client, username="admin-one"):
    hashed, salt = app.hash_password("Strong-password-123")
    with app.db_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO users(username,password_hash,salt,role,full_name) VALUES(?,?,?,?,?)",
            (username, hashed, salt, "admin", username),
        )
        uid = cur.lastrowid
    response = client.post(
        "/admin/login",
        data={"username": username, "password": "Strong-password-123"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return uid


def test_module_pages_have_operational_forms(client):
    login(client)
    for path in [
        "/admin/citizens-abroad", "/admin/travel-advisories", "/admin/emergency-alerts",
        "/admin/missions", "/admin/consular", "/admin/media-accreditation",
        "/admin/attestations", "/admin/treaties", "/admin/approvals", "/admin/biometrics",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert "Create new" in response.text
        assert "Search" in response.text
        assert "<form" in response.text


def test_create_records_across_operational_modules(client):
    uid = login(client)
    cases = [
        ("/admin/citizens-abroad", {"full_name":"Amina K","country":"Kenya","city":"Nairobi","passport_number":"UG1","phone":"1","email":"a@example.com","emergency_contact":"B","status":"active"}, "citizens_abroad"),
        ("/admin/travel-advisories", {"country":"Kenya","level":"2","title":"Exercise caution","summary":"Regional notice"}, "travel_advisories"),
        ("/admin/emergency-alerts", {"title":"Weather","message":"Heavy rain","severity":"high","audience":"all"}, "emergency_alerts"),
        ("/admin/missions", {"mission_name":"Uganda Embassy","country":"Kenya","city":"Nairobi","mission_type":"embassy","phone":"1","email":"m@example.com","address":"Road 1","status":"active"}, "diplomatic_missions"),
        ("/admin/consular", {"citizen_name":"Amina K","country":"Kenya","case_type":"lost passport","priority":"high","status":"open","notes":"Urgent"}, "consular_cases"),
        ("/admin/media-accreditation", {"applicant_name":"Reporter One","organization":"News","email":"r@example.com","phone":"1","event_name":"Briefing","status":"pending"}, "media_accreditations"),
        ("/admin/attestations", {"applicant_name":"Amina K","document_type":"certificate","reference_number":"REF1","status":"pending","notes":"Check"}, "document_attestations"),
        ("/admin/treaties", {"title":"Cooperation Agreement","partner":"Kenya","signed_date":"2026-09-16","document_reference":"TR-1","status":"active","notes":"Archive"}, "treaty_archive"),
        ("/admin/approvals", {"action_type":"publish","subject_type":"advisory","subject_id":"1","payload":"{}"}, "approval_requests"),
        ("/admin/biometrics", {"user_id":str(uid),"modality":"fingerprint","device_id":"reader-1","external_reference":"EXT1","template_hash":"hash1","status":"enrolled"}, "biometric_enrollments"),
    ]
    for path, payload, table in cases:
        response = client.post(path, data=payload, follow_redirects=False)
        assert response.status_code == 303, (path, response.status_code, response.text)
        with app.db_cursor() as cur:
            cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
            assert cur.fetchone()["c"] >= 1


def test_search_filters_module_records(client):
    login(client)
    client.post("/admin/missions", data={"mission_name":"Uganda Embassy Tokyo","country":"Japan","city":"Tokyo","mission_type":"embassy","status":"active"})
    client.post("/admin/missions", data={"mission_name":"Uganda Embassy Nairobi","country":"Kenya","city":"Nairobi","mission_type":"embassy","status":"active"})
    response = client.get("/admin/missions?q=Tokyo")
    assert "Uganda Embassy Tokyo" in response.text
    assert "Uganda Embassy Nairobi" not in response.text


def test_status_update_and_dual_control(client):
    first_uid = login(client, "admin-one")
    client.post("/admin/approvals", data={"action_type":"publish","subject_type":"advisory","subject_id":"1","payload":"{}"})
    with app.db_cursor() as cur:
        cur.execute("SELECT id FROM approval_requests ORDER BY id DESC LIMIT 1")
        request_id = cur.fetchone()["id"]

    denied = client.post(f"/admin/approvals/{request_id}/decision", data={"decision":"approved","decision_note":"self"}, follow_redirects=False)
    assert denied.status_code == 400

    client.get("/admin/logout")
    second_uid = login(client, "admin-two")
    assert second_uid != first_uid
    approved = client.post(f"/admin/approvals/{request_id}/decision", data={"decision":"approved","decision_note":"second admin"}, follow_redirects=False)
    assert approved.status_code == 303
    with app.db_cursor() as cur:
        cur.execute("SELECT status, approver_user_id FROM approval_requests WHERE id=?", (request_id,))
        row = cur.fetchone()
    assert row["status"] == "approved"
    assert row["approver_user_id"] == second_uid


def test_generic_status_update(client):
    login(client)
    client.post("/admin/media-accreditation", data={"applicant_name":"Reporter","organization":"News","status":"pending"})
    with app.db_cursor() as cur:
        cur.execute("SELECT id FROM media_accreditations ORDER BY id DESC LIMIT 1")
        record_id = cur.fetchone()["id"]
    response = client.post(f"/admin/media-accreditation/{record_id}/status", data={"status":"approved"}, follow_redirects=False)
    assert response.status_code == 303
    with app.db_cursor() as cur:
        cur.execute("SELECT status FROM media_accreditations WHERE id=?", (record_id,))
        assert cur.fetchone()["status"] == "approved"
