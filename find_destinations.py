import json
import os
import re
from datetime import datetime, timedelta
import pandas_gbq
import time

def get_project_id():
    """Get Google Cloud project ID from cache"""
    cache_file = ".bd_project_id"
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return f.read().strip()
    return None

def extract_role(text):
    """
    Tenta extrair o cargo do texto de nomeação.
    """
    if not text:
        return None
    patterns = [
        r"(?:para exercer o cargo de|para o cargo de|no cargo de|para ocupar o cargo de)\s+([^,.;]+)",
        r"(?:cargo de)\s+([^,.;]+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            role = re.sub(r'\s+', ' ', match.group(1).strip())
            return role
    return "Não identificado"

def extract_reason(text):
    """
    Tenta extrair o motivo da saída (exoneração, vacância, etc.)
    """
    if not text:
        return None
    
    text_lower = text.lower()
    
    if "posse em outro cargo inacumulável" in text_lower:
        return "Vacância (Posse outro cargo)"
    if "exoneração" in text_lower and "a pedido" in text_lower:
        return "Exoneração (A pedido)"
    if "exoneração" in text_lower:
        return "Exoneração"
    if "aposentadoria" in text_lower:
        return "Aposentadoria"
    if "falecimento" in text_lower:
        return "Falecimento"
    if "declarar vago" in text_lower or "vacância" in text_lower:
        return "Vacância"
    if "demissão" in text_lower:
        return "Demissão"
        
    return "Outro (verificar)"

def find_destinations(json_path):
    project_id = get_project_id()
    if not project_id:
        print("❌ Project ID not found in .bd_project_id")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        events = json.load(f)

    updated_count = 0
    saida_events = [e for e in events if e.get('type') == 'saída']
    total_saida = len(saida_events)
    
    print(f"Total 'saída' events to process: {total_saida}")

    for i, event in enumerate(saida_events, 1):
        name = event.get('name')
        exit_date_str = event.get('date')
        
        try:
            exit_date = datetime.strptime(exit_date_str, '%Y-%m-%d')
        except ValueError:
            continue

        # --- 1. SEARCH FOR REASON (Motivo) if not present ---
        if 'motivo' not in event:
            # Look around exit_date (± 3 days) in the original organ publications
            start_search = (exit_date - timedelta(days=3)).strftime('%Y-%m-%d')
            end_search = (exit_date + timedelta(days=3)).strftime('%Y-%m-%d')
            
            print(f"[{i}/{total_saida}] Searching REASON for {name} ({exit_date_str})...")
            
            query_reason = f"""
                SELECT texto_principal 
                FROM `basedosdados.br_imprensa_nacional_dou.secao_2` 
                WHERE LOWER(texto_principal) LIKE '%{name.lower()}%' 
                AND (LOWER(texto_principal) LIKE '%vago%' 
                     OR LOWER(texto_principal) LIKE '%vacância%'
                     OR LOWER(texto_principal) LIKE '%exonerar%'
                     OR LOWER(texto_principal) LIKE '%aposentadoria%')
                AND data_publicacao BETWEEN '{start_search}' AND '{end_search}'
                ORDER BY data_publicacao DESC
                LIMIT 1
            """
            try:
                df_reason = pandas_gbq.read_gbq(query_reason, project_id=project_id, progress_bar_type=None)
                if not df_reason.empty:
                    reason_text = df_reason.iloc[0]['texto_principal']
                    event['motivo'] = extract_reason(reason_text)
                    print(f"  -> Found Reason: {event['motivo']}")
                    updated_count += 1
                else:
                    event['motivo'] = "Não identificado"
                    print(f"  -> Reason not found.")
            except Exception as e:
                print(f"  -> Error searching reason: {e}")

        # --- 2. SEARCH FOR DESTINATION if not present ---
        if 'destino' not in event:
            start_dest = (exit_date - timedelta(days=30)).strftime('%Y-%m-%d')
            end_dest = exit_date_str

            print(f"[{i}/{total_saida}] Searching DESTINATION for {name} ({start_dest} to {end_dest})...")

            query_dest = f"""
                SELECT data_publicacao, orgao, texto_principal 
                FROM `basedosdados.br_imprensa_nacional_dou.secao_2` 
                WHERE LOWER(texto_principal) LIKE '%{name.lower()}%' 
                AND LOWER(texto_principal) LIKE '%nome%'
                AND data_publicacao BETWEEN '{start_dest}' AND '{end_dest}'
                ORDER BY data_publicacao DESC
                LIMIT 1
            """
            try:
                df_dest = pandas_gbq.read_gbq(query_dest, project_id=project_id, progress_bar_type=None)
                if not df_dest.empty:
                    row = df_dest.iloc[0]
                    event['destino'] = row['orgao']
                    event['data_nomeacao'] = str(row['data_publicacao'])
                    event['cargo_destino'] = extract_role(row['texto_principal'])
                    print(f"  -> Found Dest: {row['orgao']} | {event['cargo_destino']}")
                    updated_count += 1
                else:
                    print(f"  -> Destination not found.")
            except Exception as e:
                print(f"  -> Error searching destination: {e}")
        
        time.sleep(0.1)

    if updated_count > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        print(f"\nDone! Updated records in {json_path}.")
    else:
        print("\nNo updates made.")

if __name__ == "__main__":
    JSON_PATH = os.path.join('pipeline', 'eventos_judiciario.json')
    if os.path.exists(JSON_PATH):
        find_destinations(JSON_PATH)
    else:
        print(f"File not found: {JSON_PATH}")
