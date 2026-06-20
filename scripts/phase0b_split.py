import json, os, math
forms = json.load(open("research/forms.json", encoding="utf-8"))
content = [(k,v) for k,v in forms.items() if not v.get("is_function")]
content.sort(key=lambda kv: kv[0].lower())
N = 12
os.makedirs("research/chunks", exist_ok=True)
per = math.ceil(len(content)/N)
for i in range(N):
    chunk = content[i*per:(i+1)*per]
    out = [{"form":k, "samples":v["samples"], "songs":v["songs"]} for k,v in chunk]
    json.dump(out, open(f"research/chunks/forms_{i:02d}.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"Разбито {len(content)} форм на {N} чанков (~{per}/чанк) в research/chunks/")
