import csv, io, json, os, re, unicodedata, urllib.request

avisos = []

def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    return s.lower().strip()

def sim(v):
    return (v or "").strip().lower() in ("sim", "s", "x", "true", "1")

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")[:40]

with urllib.request.urlopen(os.environ["CSV_URL"]) as r:
    texto_csv = r.read().decode("utf-8")

itens, ids = [], set()
for n, linha in enumerate(csv.DictReader(io.StringIO(texto_csv)), start=2):
    l = {(k or "").strip(): (v or "").strip() for k, v in linha.items()}
    ref = l.get("referencia", "")
    if not ref or l.get("publicar", "sim").lower() in ("não", "nao"):
        continue

    ident = l.get("id") or slug(ref)
    if not l.get("id"):
        avisos.append(f"Linha {n}: sem id, usei '{ident}'")
    if ident in ids:
        avisos.append(f"Linha {n}: id '{ident}' repetido, linha ignorada")
        continue

    link = l.get("link", "")
    if link and not link.lower().startswith(("http://", "https://")):
        avisos.append(f"Linha {n} ({ident}): link sem http, ignorado")
        link = ""
    if "disponível em" in norm(ref).replace("disponivel", "disponível"):
        avisos.append(f"Linha {n} ({ident}): a referência contém 'Disponível em'; o link já vai na coluna link")

    try:
        ano = int(float(l.get("ano", "")))
    except ValueError:
        ano = None

    item = {"id": ident, "referencia": ref, "tipo": l.get("tipo") or "Documento",
            "tags": [t.strip() for t in re.split(r"[,;]+", l.get("tags", "")) if t.strip()]}
    if link:
        item["link"] = link
    if ano:
        item["ano"] = ano
    if l.get("nota"):
        item["nota"] = l["nota"]
    if sim(l.get("evidenciar")):
        item["evidenciar"] = True

    ids.add(ident)
    itens.append(item)

# Ordem alfabética, como na ABNT (ignora asteriscos, acentos e maiúsculas)
itens.sort(key=lambda i: (norm(i["referencia"].replace("*", "")), i.get("ano") or 0))

with open("referencias.json", "w", encoding="utf-8") as f:
    json.dump(itens, f, ensure_ascii=False, indent=2)

for a in avisos:
    print(f"::warning::{a}")
print(f"{len(itens)} referências gravadas em referencias.json")
