#!/usr/bin/env python3
"""B2 pilot smoke via API (stdlib only): register -> login -> me -> upload PDF
-> poll task -> processes -> analysis -> docx. Exit 0 = full happy path.

WSL-only (rule 7). Run with the compose stack up:
    python3 docs/coordination/smoke-api.py
See docs/coordination/reports/worker-b2-smoke.md for the captured evidence run.
"""
import json
import sys
import time
import urllib.parse
import urllib.request

BASE = "http://localhost:8000/api/v1"
STAMP = str(int(time.time()))
EMAIL = f"smoke{STAMP}@example.com"
USERNAME = f"smoke{STAMP}"
PASSWORD = "SmokePass123!"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}", flush=True)
    return ok


def req(method, path, body=None, headers=None, content_type=None):
    data = None
    h = dict(headers or {})
    if body is not None:
        if isinstance(body, dict) and content_type != "form":
            data = json.dumps(body).encode()
            h["Content-Type"] = "application/json"
        elif isinstance(body, dict):
            data = urllib.parse.urlencode(body).encode()
            h["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = body
            if content_type:
                h["Content-Type"] = content_type
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def make_pdf():
    lines = [
        "PETICAO INICIAL - ACAO DE COBRANCA",
        "Dos fatos: o reu contratou servicos e nao pagou.",
        "Do direito: Art. 319 do CPC. Art. 389 do Codigo Civil.",
        "Dos pedidos: condena ao pagamento de R$ 10.000,00.",
        "Provas: contrato e notas fiscais anexas.",
    ]
    text_ops = "".join(
        f"BT /F1 12 Tf 50 {750 - i * 20} Td ({s}) Tj ET\n" for i, s in enumerate(lines)
    )
    objs = []
    objs.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    objs.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    objs.append(
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
    )
    objs.append("4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
    stream = text_ops.encode("latin-1")
    objs.append(
        f"5 0 obj\n<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
        + stream + b"\nendstream\nendobj\n"
    )
    out = b"%PDF-1.4\n"
    offsets = []
    for o in objs:
        if isinstance(o, str):
            o = o.encode("latin-1")
        offsets.append(len(out))
        out += o
    xref_pos = len(out)
    out += f"xref\n0 {len(objs) + 1}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode("latin-1")
    out += (
        f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF".encode("latin-1")
    )
    return out


def main():
    pdf = make_pdf()
    assert pdf.startswith(b"%PDF"), "generated pdf invalid"

    s, b = req("POST", "/users/register",
               {"username": USERNAME, "email": EMAIL, "password": PASSWORD})
    if not check("1.register", s in (200, 201), f"http={s}"):
        print(b.decode()[:300]); return 1

    s, b = req("POST", "/login/access-token",
               {"username": EMAIL, "password": PASSWORD}, content_type="form")
    if not check("2.login", s == 200, f"http={s}"):
        print(b.decode()[:300]); return 1
    token = json.loads(b)["access_token"]
    H = {"Authorization": f"Bearer {token}"}

    s, b = req("GET", "/users/me", headers=H)
    if not check("3.me", s == 200, f"http={s}"):
        print(b.decode()[:300]); return 1

    boundary = "----smokeboundary1234"
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
        f"filename=\"peticao-smoke.pdf\"\r\nContent-Type: application/pdf\r\n\r\n"
    ).encode("latin-1") + pdf + f"\r\n--{boundary}--\r\n".encode("latin-1")
    s, b = req("POST", "/documents/upload", body,
               headers=H, content_type=f"multipart/form-data; boundary={boundary}")
    if not check("4.upload", s == 200, f"http={s}"):
        print(b.decode()[:500]); return 1
    up = json.loads(b)
    doc_id = up.get("task_id") or up.get("id")
    ok = check("4b.task==document", up.get("task_id") == up.get("id"), f"id={doc_id}")
    poll_url = up.get("taskStatusUrl") or f"/tasks/{doc_id}"
    print(f"    taskStatusUrl={poll_url}", flush=True)
    if not ok:
        return 1

    final = None
    t0 = time.time()
    for i in range(60):
        s, b = req("GET", poll_url, headers=H)
        if s != 200:
            check("5.poll", False, f"http={s} {b.decode()[:200]}")
            return 1
        st = json.loads(b)
        status = st.get("status")
        if status in ("COMPLETED", "FAILED"):
            final = st
            break
        time.sleep(5)
    dt = time.time() - t0
    if final is None:
        check("5.poll", False, "timeout 300s, nunca COMPLETED/FAILED")
        return 1
    if not check("5.task-COMPLETED", final.get("status") == "COMPLETED",
                 f"status={final.get('status')} em {dt:.0f}s detail={final.get('status_detail')}"):
        print(json.dumps(final)[:800]); return 1
    analysis_id = final.get("analysis_id") or doc_id

    s, b = req("GET", "/processes", headers=H)
    rows = json.loads(b) if s == 200 else []
    found = any((r.get("id") == doc_id) for r in rows)
    if not check("6.dashboard-processes", s == 200 and found,
                 f"http={s} rows={len(rows)} found={found}"):
        print(b.decode()[:500]); return 1

    s, b = req("GET", f"/analysis/{analysis_id}", headers=H)
    if not check("7.analysis", s == 200, f"http={s}"):
        print(b.decode()[:500]); return 1
    ana = json.loads(b)
    has_summary = bool(ana.get("summary") or ana.get("generatedDefenseStrategy")
                       or ana.get("generated_defense_strategy"))
    check("7b.analysis-content", has_summary, f"keys={sorted(ana.keys())[:8]}")

    s, b = req("GET", f"/analysis/{analysis_id}/docx", headers=H)
    is_docx = s == 200 and b[:2] == b"PK"
    if not check("8.docx", is_docx, f"http={s} bytes={len(b)} magic={b[:2]!r}"):
        print(b.decode()[:300] if s != 200 else ""); return 1

    failed = [r for r in RESULTS if not r[1]]
    print(f"\nSMOKE {'PASSED' if not failed else 'FAILED'}: "
          f"{len(RESULTS) - len(failed)}/{len(RESULTS)} em {dt:.0f}s proc", flush=True)
    return 0 if not failed else 1


if __name__ == "__main__":
    import urllib.error
    sys.exit(main())
