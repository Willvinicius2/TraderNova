"""Registra o progresso de um agente para o painel. Uso: python research/lab/status.py <agente> <ID|inicio>"""
import json
import sys
import time
from pathlib import Path

d = Path(__file__).resolve().parent / "status"
d.mkdir(exist_ok=True)
agent, what = sys.argv[1], sys.argv[2]
p = d / f"{agent}.json"
s = json.loads(p.read_text()) if p.exists() else {"agent": agent, "done": []}
if what != "inicio" and what not in s["done"]:
    s["done"].append(what)
s["updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
p.write_text(json.dumps(s, ensure_ascii=False))
print("ok", s)
