import json
import os
from typing import List, Dict

def apply_ground_truth(events: List[Dict], ground_truth_path: str) -> List[Dict]:
    """
    Applies ground truth overrides to the detected events.
    Rules:
    1. If a name + date matches exactly, the GT entry replaces the detected entry.
    2. If a GT entry is missing in the detected list, it is added.
    3. Events in GT are considered highly accurate.
    """
    if not os.path.exists(ground_truth_path):
        print(f"⚠️ Ground truth file not found: {ground_truth_path}")
        return events

    with open(ground_truth_path, "r", encoding="utf-8") as f:
        gt_data = json.load(f)

    print(f"📍 Aplicando Ground Truth ({len(gt_data)} registros)...")
    
    # Create a lookup map for existing events (by name and date)
    # We use name + date as the key
    event_map = {}
    for e in events:
        key = (e.get("nome", "").upper(), e.get("date", ""))
        event_map[key] = e

    added_count = 0
    overridden_count = 0

    for gt in gt_data:
        # Determine the best source for 'destino'
        # Priority: destination_matched > reason > Default
        gt_reason = gt.get("reason", "Desconhecido")
        gt_dest = gt.get("destination_matched") or gt_reason
        
        # Get organ name (prefer 'orgao' field if exists, fallback to 'trt' formatted)
        gt_orgao = gt.get("orgao")
        if not gt_orgao and gt.get("trt"):
            gt_orgao = f"trt{gt['trt']}"

        gt_event = {
            "orgao": gt_orgao,
            "destino": gt_dest if gt.get("type") == "evasão" else gt_orgao,
            "date": gt.get("date", ""),
            "mes": gt.get("date", "")[:7],
            "confidence": "ground_truth",
            "source_pdf": "DOU_AUDIT",
            "nome": gt.get("name", "").upper(),
            "role": gt.get("role", "Não identificado"),
            "ref_date": gt.get("date", ""),
            "tipo": gt.get("type", "evasão")
        }
        
        # If type is entry (ingresso), we might want to keep it or use it for matching
        # But for now the dashboard focuses on evasions (evasão)
        
        key = (gt_event["nome"], gt_event["date"])
        
        if key in event_map:
            # Override
            event_map[key].update(gt_event)
            overridden_count += 1
        else:
            # Add new (if missing)
            event_map[key] = gt_event
            added_count += 1

    final_events = list(event_map.values())
    print(f"✅ Ground Truth aplicado: {overridden_count} sobreposições, {added_count} novos eventos.")
    return final_events

if __name__ == "__main__":
    # Test loading and applying
    import sys
    events_path = sys.argv[1] if len(sys.argv) > 1 else "../site/public/data/events.json" # Not used directly here
    # This script is intended to be called by run.py
    pass
