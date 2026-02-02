import re
import spacy
from dataclasses import dataclass
from typing import List, Dict, Optional

# Lazy loader for SpaCy
_nlp = None

# List of known names for NLP seeding
KNOWN_NAMES = [
    "DIOGO COUCEIRO LEMOS", "IGOR CEZAR PEREIRA GALINDO", "EDUARDO FERREIRA DE SOUZA",
    "ANDERSON DA SILVA SANTOS", "IGOR MARCEL LEAL DE MORAIS", "RUBIA RODRIGUES RICARDO",
    "JOSUE LENNON DE SOUZA PAES", "JUN MIYAZAKI", "VITOR VALSICHI CUZIOL",
    "THAYANNE ANTAO VIEGAS", "LUCAS BATISTA LEITE DE SOUZA", "EDSON ELIAS DOS REIS",
    "ANDRÉ ADOLFO KORK ADRIAZOLA", "HUGO ARDISSON E SOUZA", "CLAUDIO SANTANA DE VASCONCELOS",
    "VICTOR HUGO ARDISSON E SOUZA", "JOAO BATISTA ARAUJO BARBOSA JUNIOR", "GHANEM YOUSSEF ARFOX",
    "GIBSON ALMEIDA JERONIMO DOS SANTOS", "ALESSANDRA OLIVEIRA DA SILVA",
    "DANIEL ALVES DA FONSECA MACIEL", "IL JOSE OLIVEIRA E REBOUCAS", "LUCAS CAMARGO CARDOSO",
    "ALIPIO CORREIA MENDES", "RAFAEL RODRIGUES DE CARVALHO", "MULLER ESPOSITO NUNES",
    "MARCO AURELIO SHIBAYAMA", "JOYCE QUEIROZ E SILVA", "JOSINALDO AMORIM DIAS DE SOUSA"
]

def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            print("⏳ Carregando modelo SpaCy (pt_core_news_sm)...")
            _nlp = spacy.load("pt_core_news_sm")
            
            # Add EntityRuler for known names
            if "entity_ruler" not in _nlp.pipe_names:
                 ruler = _nlp.add_pipe("entity_ruler", before="ner")
                 patterns = [{"label": "PER", "pattern": name} for name in KNOWN_NAMES]
                 ruler.add_patterns(patterns)
                 
            print("✅ Modelo carregado com dicionário de nomes!")
        except Exception as e:
            print(f"❌ Erro ao carregar SpaCy: {e}")
            return None
    return _nlp

@dataclass
class Event:
    trt: str
    destino: str
    date: str   # YYYY-MM-DD
    mes: str    # YYYY-MM
    confidence: str  # "confirmada"
    source_pdf: str
    nome: str = "" # New field

# Noise blacklist (names of presidents, departments, boilerplate text, etc.)
BLACKLIST = [
    "SUA PUBLICAÇÃO", "HORTA",
    "NA POLÍTICA", "DA MAGISTRATURA", "DE GESTÃO", "DO TRABALHO", "DA SECRETARIA",
    "ABAIXO INDICADO", "PELO SERVIDOR", "PELA SERVIDORA", "O CANDIDATO", "A CANDIDATA",
    "DE PESSOAL", "DE TECNOLOGIA", "DA INFORMAÇÃO", "DE SAÚDE", "DE SEGURANÇA",
    "DE TRANSPORTE", "DE APOIO", "JUDICIÁRIO", "ADMINISTRATIVO", "ESPECIALIZADA",
    "DE CARREIRA", "DE PROVIMENTO", "DE VACÂNCIA", "DE RECURSOS", "DE HUMANOS",
    "NA DATA", "DA PUBLICAÇÃO", "DO DIÁRIO", "DA UNIÃO", "DA JUSTIÇA",
    "DA DÉCIMA", "DA VIGÉSIMA", "DA SEXTA", "DA SÉTIMA", "DA OITAVA",
    "NEPOMUCENO", "MOHALLEM", "DO QUADRO",
    "ESTE CONTEÚDO", "PUBLICAÇÃO", "O DESEMBARGADOR", "A PRESIDENTE", "DÊ-SE CIÊNCIA",
    "TECNOLOGIA DA INFORMAÇÃO", "GESTAO DE PESSOAS", "OUTUBRO DE", "JANEIRO DE", 
    "FEVEREIRO DE", "MARCO DE", "ABRIL DE", "MAIO DE", "JUNHO DE", "JULHO DE", 
    "AGOSTO DE", "SETEMBRO DE", "NOVEMBRO DE", "DEZEMBRO DE",
    "SERVIDOR SEM INSTITUIÇÃO DE PENSÃO", "SEM INSTITUIÇÃO DE PENSÃO", 
    "CANDIDATO NOMEADO", "CANDIDATA NOMEADA", "AMPLA CONCORRÊNCIA", 
    "CESSAÇÃO DOS EFEITOS", "SECRETARIA DE", "DIRETORIA DE", "COORDENADORIA DE",
    "PODER JUDICIÁRIO", "JUSTIÇA DO TRABALHO", "TRIBUNAL REGIONAL",
    "PODER JUDICIÁRIO", "JUSTIÇA DO TRABALHO", "TRIBUNAL REGIONAL",
    "COM O QUE DISPÕEM", "COM O QUE DISPÕE", "ABAIXO RELACIONADO", "ABAIXO RELACIONADOS",
    "INCISO", "ALÍNEA", "ARTIGO", "ART.", "RUBRICA", "PARÁGRAFO",
    "NÍVEL SUPERIOR", "NÍVEL INTERMEDIÁRIO", "NIVEL SUPERIOR", "NIVEL INTERMEDIARIO"
]

def extract_nome(block: str) -> str:
    # List of patterns to find names in administrative acts
    patterns = [
        # Pattern for lists: 1º lugar - NAME (allowing "pela lista...")
        r"(?:\d+º\s+(?:lugar|LUGAR)\s+(?:.*?)-\s+)([A-ZÀ-Ú ][A-ZÀ-Ú ]{4,60})",
        # List format: NAME/ classification
        r"^([A-ZÀ-Ú ][A-ZÀ-Ú ]{4,60})/\s+\d+º\s+(?:colocado|COLOCADO|lugar|LUGAR|classificado|CLASSIFICADO)",
        # List format: NAME, classificado em
        r"([A-ZÀ-Ú ][A-ZÀ-Ú ]{4,60}),?\s+(?:classificado|CLASSIFICADO)\s+(?:em|EM)",
        # "ocupado por [Nome]" - refined for pelo(a) and cleanup
        r"(?:[Oo]cupado|OCUPADO)\s+(?:pelo|PELO|pela|PELA|por|POR|pl|PL|p)(?:[a-z\(\)A-Z]+)?(?:.*?)\s+(?:[Ss]ervidor|SERVIDOR)(?:a|A)?\s+[^A-ZÀ-Ú]*?([A-ZÀ-Ú][A-ZÀ-Ú ]{4,60})",
        # Broad Ocupado (Strict Uppercase Name) - Catches "ocupado por JOSINALDO"
        r"(?:[Oo]cupado|OCUPADO)\s+(?:pelo|PELO|pela|PELA|por|POR)\s+[^A-ZÀ-Ú]*?([A-ZÀ-Ú][A-ZÀ-Ú ]{4,60})",
        # "referente ao candidato abaixo relacionado: NAME"
        r"(?:[Cc]andidato|CANDIDATO)\s+(?:abaixo|ABAIXO)\s+(?:relacionado|RELACIONADO):\s*([A-ZÀ-Ú][A-ZÀ-Ú ]{4,60})",
        # Explicit "Dispensar o servidor NAME" (TRT4)
        r"(?:[Dd]ispensar|DISPENSAR)\s+(?:o|a|O|A)?\s+(?:[Ss]ervidor|SERVIDOR)(?:a|A)?\s+[^A-ZÀ-Ú]*?([A-ZÀ-Ú][A-ZÀ-Ú ]{4,60})",
        # Colon nomination (very strong signal): Nomear ... : NAME
        r"(?:[Nn]omear|NOMEAR|[Ee]xonerar|EXONERAR)(?:.{1,300}?)[:]\s*([A-ZÀ-Ú][A-ZÀ-Ú ]{4,60})",
        # Nomear NAME (Direct) - Strict Uppercase Name matches "Nomear MANOEL" but skips "Nomear o candidato"
        r"(?:[Nn]omear|NOMEAR|[Ee]xonerar|EXONERAR)\s+[^A-ZÀ-Ú]*?([A-ZÀ-Ú][A-ZÀ-Ú ]{4,60})",
         # Broad nomination with MANDATORY candidate/servidor anchor AND gap after
        r"(?:[Nn]omear|NOMEAR|[Ee]xonerar|EXONERAR|[Nn]omea[çc][ãa]o|NOMEA[ÇC][ÃA]O\s+(?:de|DE)?)(?:[^;]{1,300}?)(?:o|a|os|as|O|A|OS|AS)?\s*(?:seguintes?|SEGUINTES?)?\s*(?:[Cc]andidat|[Cc]ANDIDAT|[Ss]ervido|SERVIDO)(?:[oa]s?|[OA]S?|r|R|ra|RA|res?|RES?)(?:[^;]{1,300}?)\s+([A-ZÀ-Ú][A-ZÀ-Ú ]{4,60})",
        # Fallback broad match (careful)
        r"(?:[Tt]ornar\s+sem\s+efeito|TORNAR\s+SEM\s+EFEITO|[Dd]eclarar\s+vago|DECLARAR\s+VAGO).*?\s+(?:o|a|O|A)?\s+(?:[Ss]ervidor|SERVIDOR|[Cc]andidato|CANDIDATO|(?:[Nn]omea[çc][ãa]o|NOMEA[ÇC][ÃA]O)\s+(?:de|DE))\s+([A-ZÀ-Ú ][A-ZÀ-Ú ]{4,60})"
    ]
    
    for p in patterns:
        m = re.search(p, block) # NO IGNORECASE!
        if m:
            raw = m.group(1).strip()
            # Uppercase check: if we are relying on regex case-insensitivity, we must verify the content
            # allows for a few lowercase chars (typos) but mostly upper
            # This filters out "para exercer" matched by [A-Z ]+ in IGNORECASE mode
            if not raw or sum(1 for c in raw if c.isupper()) / (len(raw) + 1) < 0.5:
                continue

            # Clean up: stop at common delimiters after the name
            clean = re.split(r"[,;.]|\s+matr[íi]cula|\s+para\s+|\s+do\s+cargo|\s+em\s+virtude|\s+que\s+nomeou|\s+vaga\s+|\s+e\s+(?=[A-ZÀ-Ú])|\s+Art\.|vigência|decorrência|classificado|colocado|\s+cargo\s+criado|\s+cargo\s+decorrente|\s+desta\s+Universidade", raw, flags=re.IGNORECASE)[0].strip()
            
            # Clean Prefix: "Nível Superior NAME"
            clean = re.sub(r"^(?:N[ÍI]VEL\s+(?:SUPERIOR|INTERMEDI[ÁA]RIO)|T[Éé]CNICO\s+JUDICI[ÁA]RIO|ANALISTA\s+JUDICI[ÁA]RIO)\s+", "", clean, flags=re.IGNORECASE).strip()

            # Strip titles
            
            # Strip titles
            clean = re.sub(r"^(O|A)\s+(CANDIDATO|CANDIDATA|SERVIDOR|SERVIDORA)\s+", "", clean, flags=re.IGNORECASE)
            
            # Final sanity check: names should have at least 2 words and not be too generic
            if len(clean.split()) >= 2:
                upper_name = clean.upper()
                if any(noise in upper_name for noise in BLACKLIST):
                    continue
                if not upper_name.startswith("DO QUADRO"):
                    return upper_name
                
    # --- FALLBACK: SPACY NER ---
    # If regex failed, try to use Named Entity Recognition
    nlp = get_nlp()
    if nlp:
        # Limit text window to avoid processing huge blocks
        doc = nlp(block)
        candidates = []
        for ent in doc.ents:
            if ent.label_ == "PER":
                name = ent.text.strip()
                # Basic validation
                if len(name) > 3 and " " in name:
                    # Check noise
                    upper_name = name.upper()
                    if any(noise in upper_name for noise in BLACKLIST):
                        continue
                    if upper_name.startswith("DO QUADRO"):
                        continue
                    
                    # Heuristic: return the first valid PER entity found
                    # (This is simplistic; ideally we'd look for proximity to keywords)
                    candidates.append(name.title())

        if candidates:
            # Prefer longer names or matching KNOWN_NAMES exactly
            for name in candidates:
                upper = name.upper()
                if upper in KNOWN_NAMES:
                    print(f"   🎯 Dictionary Match: {upper}")
                    return upper
            return candidates[0]

    return ""

def extract_event_date(block: str) -> str:
    # Look for "a partir de DD/MM/YYYY" or "a contar de DD/MM/YYYY"
    # Removed "em" because it matches legislative dates (e.g. "Lei de 1996")
    m = re.search(r"(?:a partir de|a contar de|efeitos a partir de)\s+(\d{1,2}/\d{1,2}/\d{2,4})", block, re.IGNORECASE)
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
