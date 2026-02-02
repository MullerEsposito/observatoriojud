"""
Ingest data from DOU (Diário Oficial da União) via Base dos Dados / BigQuery

Source: basedosdados.br_imprensa_nacional_dou.secao_2
"""
import pandas_gbq
import pandas as pd
import json
import os
from datetime import datetime

# Cache directory
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_project_id():
    """Get Google Cloud project ID from cache"""
    cache_file = ".bd_project_id"
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            project_id = f.read().strip()
            if project_id:
                return project_id
    
    print("\n⚠️  Google Cloud Project ID não encontrado!")
    print("   Execute primeiro: python test_oauth.py")
    return None

def query_dou_history(
    start_date="2019-01-01",
    end_date="2024-12-31",
    use_cache=True
):
    """
    Query DOU for TRT personnel events (nominations, vacancies, etc.)
    """
    cache_name = f"dou_historical_{start_date.replace('-', '')}_{end_date.replace('-', '')}.parquet"
    cache_path = os.path.join(CACHE_DIR, cache_name)
    
    if use_cache and os.path.exists(cache_path):
        print(f"📦 Carregando dados do cache: {cache_path}")
        return pd.read_parquet(cache_path)
    
    project_id = get_project_id()
    if not project_id:
        return None
    
    print(f"🔍 Consultando DOU BigQuery ({start_date} a {end_date})...")
    print(f"🔑 Projeto: {project_id}\n")
    
    # SQL optimized for TRT personnel acts
    query = f"""
    SELECT 
        data_publicacao,
        secao,
        orgao,
        texto_completo as texto,
        url
    FROM `basedosdados.br_imprensa_nacional_dou.secao_2` 
    WHERE data_publicacao BETWEEN '{start_date}' AND '{end_date}'
      AND (
        LOWER(orgao) LIKE '%tribunal regional do trabalho%'
        OR LOWER(texto_completo) LIKE '%tribunal regional do trabalho%'
      )
      AND (
        LOWER(texto_completo) LIKE '%vago%'
        OR LOWER(texto_completo) LIKE '%exonera%'
        OR LOWER(texto_completo) LIKE '%nomea%'
        OR LOWER(texto_completo) LIKE '%posse%'
        OR LOWER(texto_completo) LIKE '%vacância%'
      )
    """
    
    try:
        print("📊 Executando query (pode levar alguns minutos)...")
        df = pandas_gbq.read_gbq(query, project_id=project_id)
        
        print(f"✅ Download concluído: {len(df)} registros encontrados")
        
        if len(df) > 0:
            df.to_parquet(cache_path, index=False)
            print(f"💾 Dados salvos em cache: {cache_path}")
            
        return df
        
    except Exception as e:
        print(f"❌ Erro ao consultar BigQuery: {e}")
        return None

def load_dou_as_text_blocks(df):
    """
    Converts DOU records to the format expected by detect_events.py
    """
    if df is None or len(df) == 0:
        return []
    
    text_blocks = []
    for _, row in df.iterrows():
        # Combine metadata into a block format
        block = f"DATA: {row['data_publicacao']}\n"
        block += f"FONTE: DOU Seção {row['secao']}\n"
        block += f"ORGAO: {row['orgao']}\n"
        block += f"URL: {row['url']}\n"
        block += "---\n"
        block += row['texto']
        
        text_blocks.append({
            'text': block,
            'source': f"DOU_{row['data_publicacao']}",
            'date': str(row['data_publicacao'])
        })
        
    return text_blocks

def main():
    print("=== DOU Historical Data Ingestion ===\n")
    
    # Default range: last 5 years
    df = query_dou_history(start_date="2019-01-01", end_date="2024-12-31")
    
    if df is not None and len(df) > 0:
        print(f"\n🚀 Próximo passo: Processar {len(df)} registros com detect_events.py")
        
        # Example of how to use with existing pipeline logic
        # blocks = load_dou_as_text_blocks(df)
        # print(f"✅ {len(blocks)} blocos de texto preparados.")
    else:
        print("\n⚠️  Nenhum dado recuperado. Verifique os filtros ou permissões.")

if __name__ == "__main__":
    main()
