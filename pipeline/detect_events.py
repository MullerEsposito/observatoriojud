import re
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class Event:
    trt: str
    destino: str
    date: str   # YYYY-MM-DD
    mes: str    # YYYY-MM
    confidence: str  # "confirmada"
    source_pdf: str
    nome: str = "" # New field

def extract_nome(block: str) -> str:
    # Patterns to find name:
    # 1. "ocupado pelo servidor X"
    # 2. "servidor(a) X" (careful with generic usage)
    # 3. "nomear/exonerar X"
    
    # Try explicit "ocupado pelo servidor" first (high confidence)
    m = re.search(r"ocupado\s+(?:pelo|pela)?\s+servidor(?:a)?\s+([A-ZÀ-Ú\s]{5,60})", block, re.IGNORECASE)
    if m:
        # cleanup: stop at comma or significant punctuation
        raw = m.group(1)
        return re.split(r"[,;]|\s+matr[íi]cula", raw, flags=re.IGNORECASE)[0].strip()
        
    # Generic "servidor(a) X" - risky, might catch "servidor do quadro"
    # Let's try simple uppercase sequence if it looks like a name
    return ""

def extract_event_date(block: str) -> str:
    # Look for "a partir de DD/MM/YYYY" or "a contar de DD/MM/YYYY"
    m = re.search(r"(?:a partir de|a contar de|em)\s+(\d{1,2}/\d{1,2}/\d{2,4})", block, re.IGNORECASE)
    if m:
        dstr = m.group(1)
        parts = dstr.split("/")
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2: year = "20" + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return ""

def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def contains_any(text: str, keywords: List[str]) -> bool:
    # Use regex with word boundaries for safer matching
    # simple text search: any(k.lower() in t for k in keywords) was too greedy
    # We join distinct keywords into a big regex pattern: \b(k1|k2|...)\b
    if not keywords: 
        return False
    
    # Escape keywords to avoid regex errors, and join them
    pattern = r"\b(" + "|".join(re.escape(k) for k in keywords) + r")\b"
    return bool(re.search(pattern, text, re.IGNORECASE))

def find_trt_context(text: str) -> str:
    # Heurística simples: tenta achar "TRT-xx" no documento; no futuro vamos mapear por caderno/metadata
    m = re.search(r"\bTRT[-\s]?\d{1,2}\b", text)
    return m.group(0).replace(" ", "") if m else "TRT"

def split_blocks(text: str) -> List[str]:
    # Quebra por linhas “fortes”; dá pra melhorar depois
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    blocks = []
    cur = []
    for ln in lines:
        cur.append(ln)
        # heurística: blocos fecham quando encontra muito espaço/indicadores
        if len(cur) >= 8 and (ln.endswith(".") or ln.endswith(":")):
            blocks.append(" ".join(cur))
            cur = []
    if cur:
        blocks.append(" ".join(cur))
    return blocks

def extract_destino(block: str) -> str:
    # tenta capturar o texto após "para o/a/em/no/na", mas ignora "em virtude/substituição/consonância/estágio/fins"
    # Negative lookahead para evitar pegar "em virtude", "em substituição", etc.
    pattern = r"\b(?:para|no|na|em)\b\s+(?!virtude|substitui|conson|estágio|fins|avalia)(.{10,120})"
    m = re.search(pattern, block, flags=re.IGNORECASE)
    if not m:
        return ""
    dest = m.group(1)
    # corta em separadores comuns
    dest = re.split(r"[.;]|,?\s+lotad[oa]|,?\s+com\s+exerc", dest, maxsplit=1)[0]
    return norm(dest)

def detect_events(text: str, rules: Dict, date_yyyy_mm_dd: str, source_pdf: str) -> List[Event]:
    blocks = split_blocks(text)
    # Valor inicial (fallback)
    trt = find_trt_context(text)
    mes = date_yyyy_mm_dd[:7]

    out: List[Event] = []
    
    # Regex para capturar cabeçalhos de TRT (ex: "Tribunal Regional do Trabalho da 23ª Região")
    # Grupos: 1 = número da região
    header_regex = r"TRIBUNAL\s+REGIONAL\s+DO\s+TRABALHO\s+DA\s+(\d{1,2})[ªº]\s+REGIÃO"

    for b in blocks:
        bnorm = norm(b)
        
        # 0) Atualiza contexto se achar cabeçalho
        m_head = re.search(header_regex, bnorm, re.IGNORECASE)
        if m_head:
            trt = f"TRT{m_head.group(1)}"
            # Geralmente o cabeçalho não tem o evento em si, mas vamos deixar passar para verificação
            # A menos que seja muito curto.
        
        # 1) saída + TI
        if not contains_any(bnorm, rules["exit_patterns"]):
            continue
        if not contains_any(bnorm, rules["ti_keywords"]):
            continue

        # 2) destino + classificação
        destino = extract_destino(bnorm)
        
        # Extrair nome da pessoa
        nome_pessoa = extract_nome(bnorm) or "Não identificado"
        
        # Extrair data de vigência
        data_efetiva = extract_event_date(bnorm) or date_yyyy_mm_dd

        # Check special case: posse em cargo inacumulável
        # Regex flexível para lidar com "posse em outro cargo público inacumulável"
        # Permite palavras opcionais entre "posse em" e "cargo" e "inacumul"
        vocab_regex = r"posse\s+em\s+(?:outro\s+)?cargo\s+(?:público\s+)?inacumul"
        is_vacancia = bool(re.search(vocab_regex, bnorm, re.IGNORECASE))

        if is_vacancia:
            # Se é vacância, é evasão, EXCETO se o destino for explicitamente outro órgão do judiciário
            if destino and contains_any(destino, rules["judiciario_keywords"]):
                continue
            
            # Se achou destino mas não é judiciário, mantemos. Se não achou, marcamos como não informado.
            # Mas cuidado: se extract_destino pegou lixo (ex: "cargo inacumulável"), 
            # não queremos mostrar isso como "Destino".
            if destino and not contains_any(destino, rules["fora_judiciario_keywords"]):
                # O regex pegou algo genérico, melhor normalizar
                destino = "Outro Órgão (Cargo Inacumulável)"
                
            if not destino:
                 destino = "Não informado (Cargo Inacumulável)"
                 
            confidence = "confirmada_vacancia"

        elif destino:
            # Caso padrão: só aceita se for destino validado como FORA do judiciário
            if contains_any(destino, rules["judiciario_keywords"]):
                continue
            if not contains_any(destino, rules["fora_judiciario_keywords"]):
                continue
            confidence = "confirmada_destino"
        
        else:
            continue


        out.append(Event(
            trt=trt,
            destino=destino,
            date=data_efetiva,
            mes=data_efetiva[:7],
            confidence=confidence,
            source_pdf=source_pdf,
            nome=nome_pessoa
        ))

    return out
