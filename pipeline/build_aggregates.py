import json
import re
import os
from collections import Counter, defaultdict
from typing import List
from datetime import datetime

STATES_MAP = {
    "ACRE": "ac", "ALAGOAS": "al", "AMAPÁ": "ap", "AMAZONAS": "am",
    "BAHIA": "ba", "CEARÁ": "ce", "DISTRITO FEDERAL": "df", "ESPÍRITO SANTO": "es",
    "GOIÁS": "go", "MARANHÃO": "ma", "MATO GROSSO": "mt", "MATO GROSSO DO SUL": "ms",
    "MINAS GERAIS": "mg", "PARÁ": "pa", "PARAÍBA": "pb", "PARANÁ": "pr",
    "PERNAMBUCO": "pe", "PIAUÍ": "pi", "RIO DE JANEIRO": "rj", "RIO GRANDE DO NORTE": "rn",
    "RIO GRANDE DO SUL": "rs", "RONDÔNIA": "ro", "RORAIMA": "rr", "SANTA CATARINA": "sc",
    "SÃO PAULO": "sp", "SERGIPE": "se", "TOCANTINS": "to"
}

def write_json(path: str, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def normalize_orgao(orgao: str) -> str:
    if not orgao: return "desconhecido"
    orgao_upper = orgao.upper().strip()

    # Órgãos Superiores e Conselhos
    if orgao_upper in ["STF", "SUPREMO TRIBUNAL FEDERAL"]:
        return "stf"
    if orgao_upper in ["CNJ", "CONSELHO NACIONAL DE JUSTIÇA"]:
        return "cnj"
    if orgao_upper in ["STJ", "SUPERIOR TRIBUNAL DE JUSTIÇA"]:
        return "stj"
    if orgao_upper in ["STM", "SUPERIOR TRIBUNAL MILITAR"]:
        return "stm"
    if orgao_upper in ["TSE", "TRIBUNAL SUPERIOR ELEITORAL"]:
        return "tse"
    if orgao_upper in ["TST", "TRIBUNAL SUPERIOR DO TRABALHO"]:
        return "tst"

    # TRT: Numerico (14) ou Prefixo (TRT14)
    if orgao.isdigit():
        return f"trt{orgao}"
    elif orgao_upper.startswith("TRT") and any(c.isdigit() for c in orgao):
        # Remove espaços e hífens para padronizar TRT 14 -> trt14
        return orgao_upper.replace(" ", "").replace("-", "").lower()

    # TRF: Regionalizado (trf1, trf2...)
    elif orgao_upper.startswith("TRF"):
        return orgao_upper.replace(" ", "").replace("-", "").lower()
    elif "TRIBUNAL REGIONAL FEDERAL" in orgao_upper:
        m = re.search(r"(\d{1,2})", orgao_upper)
        return f"trf{m.group(1)}" if m else "trf_indefinido"

    # TRE: Regionalizado (tre-sp, tre-rj...)
    elif orgao_upper.startswith("TRE"):
        state_part = re.sub(r"^TRE[\s-]*", "", orgao_upper).strip()
        if not state_part:
            return "tre_indefinido"
        abbr = STATES_MAP.get(state_part, state_part.lower())
        return f"tre-{abbr}"
    elif "TRIBUNAL REGIONAL ELEITORAL" in orgao_upper:
        found_state = None
        sorted_names = sorted(STATES_MAP.keys(), key=len, reverse=True)
        for name in sorted_names:
            if name in orgao_upper:
                found_state = STATES_MAP[name]
                break
        return f"tre-{found_state}" if found_state else "tre_indefinido"

    return orgao.lower()

def build_outputs(json_path: str, out_dir: str):
    if not os.path.exists(json_path):
        print(f"❌ Erro: {json_path} não encontrado.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        events = json.load(f)

    # Filtrar apenas evasões
    evasion_events = [e for e in events if e.get('type') == 'saída']
    
    # 1. Série Mensal
    by_month = Counter()
    for e in evasion_events:
        date = e.get('date', '2000-01-01')
        mes = date[:7]
        by_month[mes] += 1
    
    series = [{"mes": m, "evasoes": by_month[m]} for m in sorted(by_month.keys())]

    # 2. Top Órgãos (Origem)
    trts_agg = defaultdict(list)
    for e in evasion_events:
        orgao_origem = e.get('orgao', 'desconhecido')
        orgao_label = normalize_orgao(orgao_origem)
        
        # Formata o destino para exibição
        dest = e.get('destino', 'Outro Órgão')
        if not dest or dest == "Desconhecido":
            dest = "Outro Órgão"
            
        trts_agg[orgao_label].append({
            "nome": e.get('name', 'Não identificado'),
            "data": e.get('date', ''),
            "destino": dest,
            "role": e.get('role', 'Não identificado'),
            "motivo": e.get('motivo', 'Não identificado'),
            "cargo_destino": e.get('cargo_destino', '')
        })

    top_orgaos = []
    ALLOWED_PREFIXES = ["stf", "cnj", "stj", "stm", "tse", "tst", "trt", "trf", "tre"]
    
    for label, items in trts_agg.items():
        is_allowed = any(label.startswith(p) for p in ALLOWED_PREFIXES)
        if is_allowed:
            top_orgaos.append({
                "orgao": label,
                "total": len(items),
                "details": items
            })
    
    top_orgaos.sort(key=lambda x: x["total"], reverse=True)

    # 3. Top Destinos (Categorizados)
    destino_categories = Counter()
    for e in evasion_events:
        dest = e.get('destino', '').lower()
        if "falecimento" in dest:
            cat = "falecimento"
        elif "aposentadoria" in dest:
            cat = "aposentadoria"
        else:
            cat = "outros órgãos"
        destino_categories[cat] += 1
    
    top_destinos = [{"destino": k, "total": v} for k, v in destino_categories.most_common()]

    # Escrever arquivos
    write_json(os.path.join(out_dir, "series_mensal.json"), series)
    write_json(os.path.join(out_dir, "top_orgaos.json"), top_orgaos)
    write_json(os.path.join(out_dir, "top_destinos.json"), top_destinos)
    
    print(f"✅ Agregados gerados com sucesso em {out_dir}")

if __name__ == "__main__":
    build_outputs(
        json_path="pipeline/eventos_judiciario.json",
        out_dir="site/public/data"
    )
