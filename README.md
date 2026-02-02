# Observatório de Evasão de Servidores de TI do Judiciário

## 1. Objetivo do Projeto

Este projeto implementa um **observatório público** para monitorar a **evasão de servidores de Tecnologia da Informação** do poder judiciário federal, com base em **atos administrativos publicados em Diários Oficiais**.

O foco é fornecer **dados agregados, auditáveis e metodologicamente defensáveis**, sem expor dados pessoais.

---

## 2. Conceito de “Evasão” (Definição Oficial do Projeto)

Um evento é considerado **evasão** quando:

- o servidor pertence ao **quadro de um órgão do Poder Judiciário**, **E**
- exerce função/cargo relacionado à **Tecnologia da Informação**, **E**
- ocorre **saída definitiva do quadro**, **E**
- o destino é **fora do Poder Judiciário** **OU**
- ocorre **vacância por posse em cargo inacumulável** (mesmo sem destino explícito).

### ❌ Não é evasão:
- TRT → TRT  
- TRT → TRF / TJ / TRE / TST / STF / STJ / CNJ  
- Qualquer movimentação **interna ao Poder Judiciário**

---

## 3. Classificação dos Eventos

O projeto trabalha com **dois tipos de evasão confirmada**:

### 3.1 Evasão confirmada com destino explícito
Exemplo típico:
> “redistribuído para o Ministério X”

Classificação:
```json
{
  "confidence": "confirmada_destino",
  "destino": "Ministério X"
}
```

---

### 3.2 Evasão confirmada por vacância (destino não informado)
Exemplo real:
> “Declarar vago o cargo (...) em virtude de posse em cargo inacumulável”

Interpretação administrativa:
- vacância + cargo inacumulável = **saída definitiva do órgão**
- o destino existe, mas **não é publicado**

Classificação:
```json
{
  "confidence": "confirmada_vacancia",
  "destino": "Não informado"
}
```

Este tipo **é contado como evasão**, mas **não entra em rankings de destino**.

---

## 4. Arquitetura Geral

```
observatorio-evasao-ti/
├── site/
│   ├── public/data/
│   └── src/
├── pipeline/
│   ├── rules.yaml
│   ├── extract_text.py
│   ├── detect_events.py
│   ├── build_aggregates.py
│   └── run.py
└── .github/workflows/
```

---

## 5. Pipeline de Dados (Visão Lógica)

O projeto combina duas fontes de dados para garantir cobertura histórica e atualizada:

### 5.1 Fontes de Dados

1. **Série Histórica (2019-2024)**:
   - **Origem**: Diário Oficial da União (DOU) - Seção 2.
   - **Extração**: Via **BigQuery** (Google Cloud) utilizando o dataset público da [Base dos Dados](https://basedosdados.org/).
   - **Tabela**: `basedosdados.br_imprensa_nacional_dou.secao_2`.
   - **Volume**: ~9.200 portarias analisadas para detecção de evasão.

2. **Dados Recentes (Diário)**:
   - **Origem**: Diário Eletrônico da Justiça do Trabalho (DEJT).
   - **Extração**: Download manual/automático do caderno administrativo e processamento via parser PDF local.

### 5.2 Fluxo de Processamento
1. Coleta de dados (BigQuery para histórico / PDFs para atualidade).
2. Extração de texto e estruturação em blocos.
3. Aplicação de regras de detecção (`rules.yaml`).
4. Geração de JSONs agregados para o dashboard.

---

## 6. Regras Semânticas (`rules.yaml`)

O arquivo `pipeline/rules.yaml` define **toda a lógica conceitual** do projeto, sem hardcode no código.

### 6.1 Palavras-chave de TI
Qualquer termo relacionado a TI caracteriza o servidor como “TI”:
- informática
- tecnologia da informação
- sistemas
- desenvolvimento
- infraestrutura
- redes
- segurança da informação
- dados
- suporte
- governança de TI

### 6.2 Padrões de saída
- declarar vago
- vacância
- posse em cargo inacumulável
- redistribuição
- exoneração a pedido

### 6.3 Órgãos do Judiciário (exclusão)
Se o destino contiver qualquer termo do Judiciário:
- TRT, TRF, TJ, TRE
- TST, STF, STJ
- CNJ, STM, TJM

➡️ **o evento NÃO é evasão**

### 6.4 Fora do Judiciário (inclusão)
- Ministérios
- Secretarias
- Autarquias
- Bancos públicos
- Universidades
- Ministério Público
- Defensorias
- Tribunais de Contas
- Executivo / Legislativo

---

## 7. Dados Publicados (LGPD-safe)

O site publica **apenas dados agregados**, como:
- `series_mensal.json`
- `top_trts.json`
- `top_destinos.json`

Nenhum dado pessoal é divulgado.

---

## 8. Execução Local (Pipeline)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r pipeline/requirements.txt
python pipeline/run.py
```

---

## 9. Dashboard Público

- React + Vite + TypeScript
- ECharts
- GitHub Pages

URL:
https://mulleresposito.github.io/observatoriojud

---

## 10. Metodologia e Transparência

- dados oficiais
- regras explícitas
- classificação auditável
- ausência de inferência especulativa

---

## 11. Limitações

- Nem todo ato informa destino
- PDFs variam de formatação
- Heurísticas textuais

---

## 12. Próximos Passos

- Automação diária DEJT
- Extração automática de datas
- Refinamento do parser
- Expansão para outros ramos

---

## 13. Licença

Projeto de interesse público, sem identificação individual.
