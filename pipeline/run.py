import os
import yaml
from extract_text import pdf_to_text
from detect_events import detect_events
from build_aggregates import build_outputs

# Onde o site lê os dados
# Se estiver dentro de 'pipeline', volta um nível
PROJECT_ROOT = ".." if os.path.basename(os.getcwd()) == "pipeline" else "."
OUT_DIR = os.path.join(PROJECT_ROOT, "site", "public", "data")

def main():
    # 1) regras
    # Assumes running from pipeline directory or project root
    rules_path = "rules.yaml" if os.path.exists("rules.yaml") else os.path.join("pipeline", "rules.yaml")
    with open(rules_path, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f)

    events = []

    # 2) Process PDFs (DEJT)
    pdf_dir = "pdfs" if os.path.exists("pdfs") else os.path.join("pipeline", "pdfs")
    date_pdf = os.environ.get("DATA_REF", "2026-01-30")

    if os.path.exists(pdf_dir) and os.path.isdir(pdf_dir):
        print("📄 Processando PDFs do DEJT...")
        for name in os.listdir(pdf_dir):
            if not name.lower().endswith(".pdf"):
                continue
            path = os.path.join(pdf_dir, name)
            text = pdf_to_text(path)
            events.extend(detect_events(text, rules, date_pdf, source_pdf=name))

    # 3) Process DOU Historical Data (BigQuery Cache)
    # We use the specific functions from our ingestion script
    from ingest_dou import query_dou_history, load_dou_as_text_blocks
    
    print("\n🔍 Verificando dados históricos do DOU...")
    # This will load from cache if already downloaded (9,187 records)
    df_dou = query_dou_history(start_date="2019-01-01", end_date="2024-12-31", use_cache=True)
    
    if df_dou is not None and len(df_dou) > 0:
        print(f"⌛ Processando {len(df_dou)} registros do DOU...")
        dou_blocks = load_dou_as_text_blocks(df_dou)
        
        # We can process in batches if needed, but 9k is manageable in memory
        for i, block in enumerate(dou_blocks):
            if i % 500 == 0 and i > 0:
                print(f"   ... {i} registros processados")
                
            # Process each DOU record as a separate source
            # detect_events extraction logic is the same for text
            dou_events = detect_events(
                block['text'], 
                rules, 
                block['date'], 
                source_pdf=f"DOU_{block['date']}"
            )
            events.extend(dou_events)

    # 4) Save results
    os.makedirs(OUT_DIR, exist_ok=True)
    build_outputs(events, OUT_DIR)

    print(f"\n✨ FINALIZADO ✨")
    print(f"Total de eventos detectados: {len(events)}")
    print(f"JSONs atualizados em: {OUT_DIR}")

if __name__ == "__main__":
    main()
