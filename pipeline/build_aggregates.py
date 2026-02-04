import json
from collections import Counter, defaultdict
from typing import List
from datetime import datetime
from detect_events import Event

def write_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def deduplicate_events(events: List[Event]) -> List[Event]:
    """
    Remove eventos duplicados para o mesmo servidor em um intervalo de 30 dias.
    Mantém apenas o registro mais antigo no período.
    """
    # Ordena por nome e data para processamento sequencial
    events.sort(key=lambda x: (x.nome, x.date))
    
    deduplicated = []
    last_event_by_name = {} # (nome, trt, tipo) -> (data, ref_date)
    
    print(f"🧹 Deduplicando {len(events)} eventos...")
    removed_count = 0
    
    for e in events:
        if not e.nome or e.nome == "Não identificado":
            deduplicated.append(e)
            continue
            
        try:
            current_date = datetime.strptime(e.date, "%Y-%m-%d")
        except:
            # Fallback se a data estiver em formato ruim
            deduplicated.append(e)
            continue
            
        # Key includes TRT and type to allow fast transitions between different seats
        key = (e.nome, e.trt, e.tipo)
        
        if key in last_event_by_name:
            last_date, last_ref_date = last_event_by_name[key]
            
            # Condição 1: Mesma data de referência (citação explícita)
            if e.ref_date and (e.ref_date == last_ref_date or e.ref_date == last_date.strftime("%Y-%m-%d")):
                removed_count += 1
                continue
                
            # Condição 2: Regra de janela de 30 dias para o MESMO cargo/local
            if (current_date - last_date).days < 30:
                removed_count += 1
                continue
        
        deduplicated.append(e)
        last_event_by_name[key] = (current_date, e.ref_date)
        
    if removed_count > 0:
        print(f"✅ {removed_count} duplicatas removidas (regra de 30 dias).")
    
    return deduplicated

def match_destinations(events: List[Event]) -> List[Event]:
    """
    Tenta associar destinos para eventos de evasão baseando-se em nomeações
    ocorridas em uma janela de 45 dias.
    """
    # Filtra por tipo
    evasions = [e for e in events if e.tipo == "evasão"]
    entries = [e for e in events if e.tipo == "ingresso"]
    
    # Mapeia ingressos por nome para busca rápida: nome -> lista de (data_obj, trt)
    entry_map = defaultdict(list)
    for en in entries:
        try:
            d_obj = datetime.strptime(en.date, "%Y-%m-%d")
            entry_map[en.nome].append((d_obj, en.trt))
        except:
            continue
            
    matched_count = 0
    for ev in evasions:
        # Só tentamos se o destino é genérico/desconhecido
        is_generic = "Não informado" in ev.destino or "Outro Órgão" in ev.destino or ev.destino == "Desconhecido"
        if not is_generic:
            continue
            
        if ev.nome in entry_map:
            try:
                ev_date = datetime.strptime(ev.date, "%Y-%m-%d")
            except:
                continue
                
            # Procura nomeação ocorrida em uma janela de 45 dias
            for en_date, en_trt in entry_map[ev.nome]:
                diff = abs((ev_date - en_date).days)
                if diff <= 45:
                    # Helper to format organ name
                    def format_organ(o):
                        return f"TRT{o}" if o.isdigit() else o

                    if ev.trt == en_trt:
                        ev.destino = f"Interno ({format_organ(en_trt)})"
                    else:
                        ev.destino = format_organ(en_trt)
                        
                    ev.confidence += "_matched"
                    matched_count += 1
                    break
                    
    if matched_count > 0:
        print(f"🎯 {matched_count} destinos identificados via cruzamento de nomeações.")
        
    return evasions

def categorize_destino(destino: str) -> str:
    """
    Categoriza destinos em 3 grupos:
    - falecimento
    - aposentadoria
    - outros órgãos
    """
    destino_lower = destino.lower()
    
    if "falecimento" in destino_lower or "falec" in destino_lower or "óbito" in destino_lower:
        return "falecimento"
    elif "aposentadoria" in destino_lower or "aposentar" in destino_lower:
        return "aposentadoria"
    else:
        return "outros órgãos"

def build_outputs(events: List[Event], out_dir: str):
    from collections import Counter, defaultdict
    
    # 1. Deduplicação
    events = deduplicate_events(events)
    
    # 2. Match de Destinos
    evasion_events = match_destinations(events)
    
    # série mensal
    by_month = Counter(e.mes for e in evasion_events)
    series = [{"mes": m, "evasoes": by_month[m]} for m in sorted(by_month.keys())]

    # top trts with details
    trts_agg = defaultdict(list)
    for e in evasion_events:
        # Formata o destino para exibição amigável
        dest_display = e.destino
        if "Não informado" in dest_display or "Desconhecido" in dest_display:
            dest_display = "Outro Órgão"

        trts_agg[e.trt].append({
            "nome": e.nome,
            "data": e.date,
            "destino": dest_display
        })
        
    # Agrega e formata o ranking
    top_orgaos = []
    for orgao, items in trts_agg.items():
        # TRT: Numerico (14) ou Prefixo (TRT14)
        if orgao.isdigit():
            orgao_label = f"trt{orgao}"
        elif orgao.upper().startswith("TRT") and any(c.isdigit() for c in orgao):
            orgao_label = orgao.lower()
            
        # TRF: Prefixo TRF (TRF1)
        elif orgao.upper().startswith("TRF"):
            orgao_label = orgao.lower()
            
        # TRE: Prefixo TRE (TRE SP -> tre_sp)
        elif orgao.upper().startswith("TRE"):
            # Normalize spaces/dashes to underscore
            clean_tre = orgao.replace(" ", "_").replace("-", "_")
            orgao_label = clean_tre.lower()
            
        # Genérico ou outros
        elif orgao.upper() == "TRT":
            orgao_label = "trt_indefinido"
        else:
            # Outros órgãos (mantém original, mas talvez lowercase?)
            orgao_label = orgao.lower() if len(orgao) < 10 else orgao

        top_orgaos.append({
            "orgao": orgao_label,
            "total": len(items),
            "details": items
        })
    
    top_orgaos.sort(key=lambda x: x["total"], reverse=True)
    top_orgaos = top_orgaos[:50] # Increase limit to show more organs

    # top destinos
    destino_categories = Counter()
    for e in evasion_events:
        category = categorize_destino(e.destino)
        destino_categories[category] += 1
    
    top_destinos = [{"destino": k, "total": v} for k, v in destino_categories.most_common()]

    write_json(f"{out_dir}/series_mensal.json", series)
    write_json(f"{out_dir}/top_orgaos.json", top_orgaos)
    write_json(f"{out_dir}/top_destinos.json", top_destinos)
