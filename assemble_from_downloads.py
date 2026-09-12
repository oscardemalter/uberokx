import pathlib, zipfile
SRC = pathlib.Path.home() / "storage" / "shared" / "Download"
ROOT = pathlib.Path.home() / "uberokx" / "Ubergestalt2026"
MAP = {
 "backend__config":"backend/config.py",
 "backend__auth":"backend/auth.py",
 "backend__main":"backend/main.py",
 "backend__services__agents":"backend/services/agents.py",
 "backend__services__llm":"backend/services/llm.py",
 "backend__services__jarvis":"backend/services/jarvis.py",
 "backend__services__quant":"backend/services/quant.py",
 "backend__services__okx_connect":"backend/services/okx_connect.py",
 "backend__services__exchange":"backend/services/exchange.py",
 "backend__services__signals_native":"backend/services/signals_native.py",
 "backend__services__freqtrade_bridge":"backend/services/freqtrade_bridge.py",
 "backend__services__academy":"backend/services/academy.py",
 "backend__services__testimonials":"backend/services/testimonials.py",
 "backend__services__verification_gate":"backend/services/verification_gate.py",
 "backend__templates__login":"backend/templates/login.html",
 "backend__templates__dashboard":"backend/templates/dashboard.html",
 "backend__static__css__style":"backend/static/css/style.css",
 "backend__static__js__app":"backend/static/js/app.js",
 "backend__static__manifest":"backend/static/manifest.json",
 "backend__static__sw":"backend/static/sw.js",
 "pine__uberox_emitter_v6":"pine/uberox_emitter_v6.pine",
 "uberkox__core__signal_contract":"uberkox/core/signal_contract.json",
 "requirements":"requirements.txt",
 "env.example":".env.example",
 "README":"README.md",
 "assemble_uberox":"assemble_uberox.py",
}
found, missing = [], []
for stem, rel in MAP.items():
    src = SRC / (stem + ".txt")
    if src.is_file():
        dst = ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        found.append(rel)
    else:
        missing.append(rel)
(ROOT/"backend").mkdir(parents=True, exist_ok=True)
(ROOT/"backend"/"__init__.py").write_text("", encoding="utf-8")
(ROOT/"backend"/"services").mkdir(parents=True, exist_ok=True)
(ROOT/"backend"/"services"/"__init__.py").write_text("", encoding="utf-8")
print("OK écrits :", len(found))
print("MANQUANTS :", missing if missing else "aucun")
with zipfile.ZipFile(pathlib.Path.home()/ "uberokx" / "UberOKX_final.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(ROOT.rglob("*")):
        if f.is_file(): z.write(f, f.relative_to(ROOT.parent).as_posix())
print("ZIP OK : ~/uberokx/UberOKX_final.zip")
