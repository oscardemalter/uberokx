import re, pathlib
root = pathlib.Path(".")
txt = pathlib.Path("UberOKX.txt").read_text(encoding="utf-8")
parts = re.split(r"(?m)^===== +(.+?) +===== *$", txt)
i, n = 1, 0
while i + 1 < len(parts):
    header, body = parts[i].strip(), parts[i+1]
    i += 2
    if header.startswith("00_"):
        continue
    name = re.sub(r"^\d+_", "", header)
    if re.match(r"u\d+\.txt$", name):
        print("FORMAT ANCIEN (u1..u7) : dis à Qwen « renvoie le bloc final »")
        raise SystemExit(1)
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.strip("\n") + "\n", encoding="utf-8")
    n += 1
    print("wrote", name)
print("DONE:", n, "fichiers")
