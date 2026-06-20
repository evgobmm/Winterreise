import json, glob, os, sys, time
sys.path.insert(0, 'scripts')
import word_check_lib as wcl
rep = json.load(open("research/verify_full_report.json", encoding="utf-8"))
FN = {"Adelung": wcl.src_adelung, "Campe": wcl.src_campe, "Grimm": wcl.src_grimm,
      "DWDS": wcl.src_dwds, "Goethe": wcl.src_goethe}
# целевые: толковые DE с чужой статьёй
targets = {}
for src in ("Grimm", "Campe", "DWDS", "Goethe"):
    for L in rep.get(src, []):
        targets.setdefault(L, set()).add(src)
def safe(L): return ''.join(c if c.isalnum() or c in '-_' else '_' for c in L)
n=0; fixed=0; reclass=0
for L, srcs in targets.items():
    p=f"research/tables/{safe(L)}.json"
    if not os.path.exists(p): continue
    t=json.load(open(p,encoding="utf-8")); raw=f"research/raw/{L}"; ch=False
    for i,s in enumerate(t["sources"]):
        for src in srcs:
            if src in s["name"]:
                t["sources"][i]=FN[src](L, raw); ch=True; n+=1
                if "❌" in t["sources"][i]["status"]: reclass+=1
                else: fixed+=1
    if ch: json.dump(t, open(p,"w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"пере-фетч {n} ячеек толковых; исправлено-на-верную {fixed}, честно-нет-статьи {reclass}")
