"""
Script para descobrir destinos de evasão cruzando nomeações e vacâncias.
Lógica ampliada e normalizada.
"""
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict
import unicodedata

def normalize_name(name):
    if not name: return ""
    # Remove acentos e coloca em maiúsculas
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
    name = name.upper().strip()
    return name

def match_destinations():
    print("Iniciando cruzamento de destinos (lógica refinada)...")
    
    with open('pipeline/ground_truth.json', 'r', encoding='utf-8') as f:
        events = json.load(f)
        
    ingressos = []
    evasoes_para_match = []
    
    for e in events:
        if e['type'] == 'ingresso':
            ingressos.append(e)
        elif e['type'] == 'evasão' and ('posse' in e.get('reason', '').lower() or 'exoneração' in e.get('reason', '').lower()):
            evasoes_para_match.append(e)
            
    print(f"Total de ingressos: {len(ingressos)}")
    print(f"Total de evasões passíveis de match: {len(evasoes_para_match)}")
    
    ingressos_por_nome = defaultdict(list)
    for ing in ingressos:
        norm_name = normalize_name(ing['name'])
        ingressos_por_nome[norm_name].append(ing)
        
    matched_count = 0
    matched_names = []

    # Janela ampliada para 45 dias
    WINDOW = 45

    for eva in evasoes_para_match:
        eva_date = datetime.strptime(eva['date'], '%Y-%m-%d')
        eva_name = normalize_name(eva['name'])
        
        candidates = ingressos_por_nome.get(eva_name, [])
        best_match = None
        
        for cand in candidates:
            cand_date = datetime.strptime(cand['date'], '%Y-%m-%d')
            diff = abs((cand_date - eva_date).days)
            
            # Match se diferença <= WINDOW dias
            if diff <= WINDOW:
                # Se for o mesmo órgão, é movimento interno (promoção/novo cargo)
                if cand['trt'] == eva['trt']:
                    dest_str = f"Interno (TRT{cand['trt']})"
                else:
                    dest_str = f"TRT{cand['trt']}"
                
                # Se for o match mais próximo em dias
                if not best_match or diff < abs((datetime.strptime(best_match['date'], '%Y-%m-%d') - eva_date).days):
                    best_match = cand
                    iva_dest = dest_str
        
        if best_match:
            eva['destination_matched'] = iva_dest
            eva['details'] = f"{eva.get('details', '')} | Destino identificado: {iva_dest}".strip(' | ')
            matched_count += 1
            matched_names.append(f"{eva_name} ({eva['date']}) -> {iva_dest}")

    # Salva a base com os matches
    with open('pipeline/ground_truth.json', 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
        
    for m in matched_names:
        print(f"✅ Match: {m}")
        
    print(f"\nFinalizado! {matched_count} destinos identificados.")

if __name__ == "__main__":
    match_destinations()
