"""Polish PRESIDENT artwork sizing and keep Staff Admin desktop layout."""
from html import escape
import president_expanded_admin as expanded
import ung_president as core
from fastapi.responses import HTMLResponse


def apply_desktop_admin_fix():
    # Public home: larger circles with an inset artwork stage so no emblem text is clipped.
    core.CSS += """
    .badge-row{gap:42px;padding:64px 24px 30px;align-items:flex-start}
    .badge-item{max-width:310px;width:310px}
    .badge-circle{position:relative;width:286px;height:286px;background:#07152a;display:flex;align-items:center;justify-content:center;padding:26px;isolation:isolate}\n    .badge-circle::before{content:"";position:absolute;left:8px;right:8px;top:50%;height:78px;transform:translateY(-50%);background:linear-gradient(to bottom,#000 0 33.333%,#d71920 33.333% 66.666%,#fcdc04 66.666% 100%);z-index:2;pointer-events:none}\n    .badge-item:nth-child(2) .badge-circle img{z-index:3;clip-path:circle(42% at 50% 50%)}\n    .badge-item:nth-child(3) .badge-circle::before{display:none}\n    .badge-item:nth-child(3) .badge-circle img{z-index:3;object-fit:contain;padding:4px;box-sizing:border-box}\n    .badge-circle img{position:relative;z-index:1;background:transparent}
    .badge-circle img{position:relative;z-index:1;width:100%;height:100%;object-fit:contain;object-position:center center;display:block;border-radius:50%;background:transparent}
    @media(max-width:900px){
      .badge-row{gap:34px}
      .badge-item{max-width:290px;width:290px}
      .badge-circle{width:268px;height:268px;padding:24px}
    }
    """

    def desktop_shell(title: str, user, body: str):
        return HTMLResponse(f"""<!doctype html><html><head>
        <meta name='viewport' content='width=1180, initial-scale=0.32, minimum-scale=0.25'>
        <title>{escape(title)} · UNG-PRESIDENT</title><style>
        html,body{{margin:0;min-width:1180px;background:#f6f3ec;color:#10203a;font-family:Arial,sans-serif}}
        .desktop-shell{{display:grid;grid-template-columns:260px 920px;width:1180px;min-height:100vh;align-items:stretch}}
        aside{{width:260px;box-sizing:border-box;background:#07152a;padding:28px 18px;overflow:auto;min-height:100vh}}
        aside a{{display:block;color:#fff;text-decoration:none;padding:10px 0;font-size:14px}}
        .admin-brand{{text-align:center;margin:0 0 22px}}
        .admin-seal{{display:block;width:112px;height:112px;object-fit:contain;margin:0 auto 14px}}
        .admin-name{{color:white;font-weight:800;font-size:17px;letter-spacing:.5px}}
        main{{width:920px;box-sizing:border-box;padding:34px 38px}}
        .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}
        .card{{background:white;border:1px solid #ddd4c5;border-radius:10px;padding:18px}}
        h1{{border-bottom:2px solid #b5943d;padding-bottom:10px}}
        table{{width:100%;border-collapse:collapse;background:#fff}}
        th,td{{padding:10px;border-bottom:1px solid #eee;text-align:left;font-size:13px;vertical-align:top}}
        input,textarea,select{{width:100%;box-sizing:border-box;padding:10px;border:1px solid #cfc7ba;border-radius:6px;font-size:15px}}
        textarea{{min-height:88px}}label{{font-size:13px;font-weight:700;display:block;margin-bottom:5px}}
        button{{padding:10px 14px;border:0;border-radius:6px;background:#10203a;color:white;font-weight:700}}
        .form-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
        .toolbar{{display:flex;gap:8px;align-items:end;flex-wrap:wrap;margin:12px 0}}
        .toolbar input{{min-width:230px}}.muted{{color:#667085}}.actions{{display:flex;gap:6px;flex-wrap:wrap}}
        .actions form{{display:inline}}.actions button{{padding:6px 9px;font-size:12px}}
        </style></head><body><div class='desktop-shell'><aside>
        <div class='admin-brand'><img class='admin-seal' src='data:image/png;base64,{core.PRES_SEAL_B64}' alt='Presidential Seal'><div class='admin-name'>UNG-PRESIDENT</div></div>
        <a href='/admin'>Dashboard</a>{expanded._nav()}<a href='/admin/logout' style='color:#ff9a9a'>Logout</a>
        </aside><main><h1>{escape(title)}</h1><p>Signed in as <strong>{escape(user['username'])}</strong> ({escape(user['role'])})</p>{body}</main></div></body></html>""")
    expanded._shell = desktop_shell
