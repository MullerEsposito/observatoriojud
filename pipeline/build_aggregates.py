import json
from collections import Counter, defaultdict
from typing import List
from detect_events import Event

def write_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def build_outputs(events: List[Event], out_dir: str):
    # série mensal
    by_month = Counter(e.mes for e in events)
    series = [{"mes": m, "evasoes": by_month[m]} for m in sorted(by_month.keys())]

    # top trts
    # by_trt = Counter(e.trt for e in events)
    # top_trts = [{"trt": k, "total": v} for k, v in by_trt.most_common(20)]
    
    # New aggregation with details
    trts_agg = defaultdict(list)
    for e in events:
        trts_agg[e.trt].append({
            "nome": e.nome,
            "data": e.date  # YYYY-MM-DD
        })
        
    # Sort by total count desc
    top_trts = []
    for trt, items in trts_agg.items():
        top_trts.append({
            "trt": trt,
            "total": len(items),
            "details": items
        })
    
    top_trts.sort(key=lambda x: x["total"], reverse=True)
    top_trts = top_trts[:20]

    # top destinos
    by_dest = Counter(e.destino for e in events)
    top_destinos = [{"destino": k, "total": v} for k, v in by_dest.most_common(30)]

    write_json(f"{out_dir}/series_mensal.json", series)
    write_json(f"{out_dir}/top_trts.json", top_trts)
    write_json(f"{out_dir}/top_destinos.json", top_destinos)
