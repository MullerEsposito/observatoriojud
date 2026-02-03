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
    "MARCO AURELIO SHIBAYAMA", "JOYCE QUEIROZ E SILVA", "JOSINALDO AMORIM DIAS DE SOUSA",
    "LUIS CARLOS MOREIRA SILVA JUNIOR"
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
    ref_date: str = "" # Reference publication date cited in text
    tipo: str = "evasão" # "evasão" or "ingresso"

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
        # Colon nomination (very strong signal): Nomear ... : NAME
        r"(?:[Nn]omear|NOMEAR|[Ee]xonerar|EXONERAR)\b(?:.{1,300}?)[:]\s*([A-ZÀ-Ú][A-ZÀ-Ú ]{4,60})",
        # Nomear NAME (Direct) - Robust for legal noise
        r"(?:[Nn]omear|NOMEAR|[Ee]xonerar|EXONERAR)\b.{1,500}?\b([A-ZÀ-Ú][A-ZÀ-Ú ]{12,60})\b",
         # Broad nomination with MANDATORY candidate/servidor anchor AND gap after
        r"(?:[Nn]omear|NOMEAR|[Ee]xonerar|EXONERAR|[Nn]omea[çc][ãa]o\b|NOMEA[ÇC][ÃA]O\s+(?:de|DE)?)(?:[^;]{1,300}?)(?:o|a|os|as)?\s*(?:seguintes?)?\s*(?:[Cc]andidat|[Ss]ervido)(?:[oa]s?|r|ra|res?)(?:[^;]{1,300}?)\s+([A-ZÀ-Ú][A-ZÀ-Ú ]{4,60})",
        # Fallback broad match (careful)
        r"(?:[Tt]ornar\s+sem\s+efeito|TORNAR\s+SEM\s+EFEITO|[Dd]eclarar\s+vago|DECLARAR\s+VAGO)\b.*?\s+(?:o|a)?\s+(?:[Ss]ervidor|[Cc]andidato|(?:[Nn]omea[çc][ãa]o)\s+(?:de|DE))\s+([A-ZÀ-Ú ][A-ZÀ-Ú ]{4,60})",
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
    # Heurística: tenta achar "TRT-xx" ou o nome por extenso
    m = re.search(r"\bTRT[-\s]?(\d{1,2})\b", text, re.IGNORECASE)
    if m:
        return f"TRT{m.group(1)}"
        
    m2 = re.search(r"TRIBUNAL\s+REGIONAL\s+DO\s+TRABALHO\s+DA\s+(\d{1,2})", text, re.IGNORECASE)
    if m2:
        return f"TRT{m2.group(1)}"
        
    return "TRT"

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
    header_regex = r"TRIBUNAL\s+REGIONAL\s+DO\s+TRABALHO\s+DA\s+(\d{1,2})\b"

    for b in blocks:
        bnorm = norm(b)
        
        # 0) Atualiza contexto se achar cabeçalho
        m_head = re.search(header_regex, bnorm, re.IGNORECASE)
        if m_head:
            trt = f"TRT{m_head.group(1)}"
            # Geralmente o cabeçalho não tem o evento em si, mas vamos deixar passar para verificação
            # A menos que seja muito curto.
        
        # 1) filtros de exclusão (Retificação)
        if contains_any(bnorm, rules.get("skip_patterns", [])):
            continue
            
        # 2) Identificar se é ENTRADA (Ingresso) vs SAÍDA (Evasão)
        is_ingresso = contains_any(bnorm, rules.get("entry_patterns", []))
        is_saida = contains_any(bnorm, rules["exit_patterns"])
        
        if not is_saida and not is_ingresso:
            continue
            
        if not contains_any(bnorm, rules["ti_keywords"]):
            continue

        # 4) Extrair nome da pessoa (O SUJEITO)
        nome_pessoa = extract_nome(bnorm) or "Não identificado"

        # 5) destino + classificação
        destino = extract_destino(bnorm)
        data_efetiva = extract_event_date(bnorm) or date_yyyy_mm_dd

        # Categorização de motivos
        # PRIORIDADE: se é ingresso (Nomeação), marcamos como tal primeiro.
        # Se também tiver exit_patterns (ex: "Nomear... vago por aposentadoria de X"),
        # o ingresso vence para o TI principal.
        if is_ingresso:
            tipo = "ingresso"
            confidence = "confirmada_ingresso"
        elif is_saida:
            tipo = "evasão"
            confidence = "confirmada_saida"
            
            # Checar motivos específicos APENAS se o nome for o sujeito
            # Heurística: "aposentadoria de [NOME]" ou similar
            # Vamos ver se "aposentadoria" e "X" estão próximos
            has_aposentar = "aposentadoria" in bnorm or "aposentar" in bnorm
            has_falecer = "falecimento" in bnorm or "falecer" in bnorm
            
            if has_aposentar:
                # Checa se o termo aposentadoria está perto do nome extraído
                # (evita pegar aposentadoria de terceiros citada no texto)
                aposent_regex = rf"(?:aposentadoria|aposentar).{{0,50}}\b{re.escape(nome_pessoa)}\b"
                if re.search(aposent_regex, bnorm, re.IGNORECASE):
                    destino = "Aposentadoria"
                    confidence = "confirmada_aposentar"
                elif "conceder aposentadoria" in bnorm.lower():
                    # Caso genérico de portaria de concessão
                    destino = "Aposentadoria"
                    confidence = "confirmada_aposentar"
            
            if has_falecer and confidence != "confirmada_aposentar":
                falecer_regex = rf"(?:falecimento|falecer).{{0,50}}\b{re.escape(nome_pessoa)}\b"
                if re.search(falecer_regex, bnorm, re.IGNORECASE):
                    destino = "Falecimento"
                    confidence = "confirmada_falecer"

            # Se não foi aposentadoria/falecimento, checa vacância por posse
            if confidence == "confirmada_saida":
                vocab_regex = r"posse\s+em\s+(?:outro\s+)?cargo\s+(?:público\s+)?inacumul"
                is_vacancia = bool(re.search(vocab_regex, bnorm, re.IGNORECASE))

                if is_vacancia:
                    if destino and contains_any(destino, rules["judiciario_keywords"]):
                        continue
                    if destino and not contains_any(destino, rules["fora_judiciario_keywords"]):
                        destino = "Outro Órgão (Cargo Inacumulável)"
                    if not destino:
                        destino = "Não informado (Cargo Inacumulável)"
                    confidence = "confirmada_vacancia"
                elif destino:
                    if contains_any(destino, rules["judiciario_keywords"]):
                        continue
                    if not contains_any(destino, rules["fora_judiciario_keywords"]):
                        continue
                    confidence = "confirmada_destino"
                else:
                    # Se não achou motivo nem destino validado, ignoramos para o dashboard
                    continue
        else:
            continue

        out.append(Event(
            trt=trt,
            destino=destino or "Desconhecido",
            date=data_efetiva,
            mes=data_efetiva[:7],
            confidence=confidence,
            source_pdf=source_pdf,
            nome=nome_pessoa,
            ref_date=extract_cited_date(bnorm, nome_pessoa) or "",
            tipo=tipo
        ))

    return out

def extract_cited_date(block: str, name: str) -> str:
    """
    Looks for strings like 'publicada em 30 de setembro de 2021' following the name.
    """
    if not name or name == "Não identificado":
        return ""
        
    # Find name position
    pos = block.upper().find(name.upper())
    if pos == -1:
        return ""
        
    # Look at a window after the name (300 chars)
    window = block[pos:pos+300]
    
    # Pattern: publicada em DD de MONTH de YYYY
    # Or: publicada em DD/MM/YYYY
    # Regex flexível para o formato de data por extenso
    m = re.search(r"publicada?\s+em\s+(\d{1,2}/\d{1,2}/(?:\d{2,4}))", window, re.IGNORECASE)
    if not m:
        # Tenta formato por extenso: 30 de setembro de 2021
        m = re.search(r"publicada?\s+em\s+(\d{1,2})\s+de\s+(janeiro|fevereiro|março|marco|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+(\d{4})", window, re.IGNORECASE)
        if m:
            day = m.group(1).zfill(2)
            month_name = m.group(2).lower()
            year = m.group(3)
            
            months = {
                "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03", "abril": "04",
                "maio": "05", "junho": "06", "julho": "07", "agosto": "08", "setembro": "09",
                "outubro": "10", "novembro": "11", "dezembro": "12"
            }
            month = months.get(month_name, "01")
            return f"{year}-{month}-{day}"
    
    if m:
        dstr = m.group(1)
        parts = dstr.split("/")
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2: year = "20" + year
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
    return ""
