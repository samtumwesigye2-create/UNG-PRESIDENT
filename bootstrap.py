"""One-time production bootstrap for the first HR administrator enrollment code."""
import secrets
import ung_president as core


def ensure_initial_hr_code():
    core.init_db()
    with core.db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM users")
        users = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM hr_codes WHERE is_used=0")
        unused = cur.fetchone()["n"]
    if users or unused:
        return None
    code = "-".join(secrets.token_hex(2).upper() for _ in range(3))
    with core.db_cursor(commit=True) as cur:
        cur.execute("INSERT INTO hr_codes (code_hash, role, assigned_name, note) VALUES (?, ?, ?, ?)",(core.hash_hr_code(code), "admin", "Initial Administrator", "One-time production bootstrap"))
    print(f"UNG-PRESIDENT INITIAL HR CODE: {code}", flush=True)
    return code


if __name__ == "__main__":
    ensure_initial_hr_code()
    import registration_response_fix
    registration_response_fix.apply_registration_response_fix()
    import president_expanded_admin
    import desktop_admin_fix
    desktop_admin_fix.apply_desktop_admin_fix()
    president_expanded_admin.apply_expanded_admin()
    import president_nsc
    president_nsc.apply_nsc(core)
    import president_un_affairs
    president_un_affairs.apply_un_affairs(core)
    import uvicorn
    import password_reset
    uvicorn.run(password_reset.core.app, host="0.0.0.0", port=int(__import__('os').environ.get("PORT", "8000")))
