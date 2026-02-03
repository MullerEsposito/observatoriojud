# Observatório de Evasão de Servidores de TI do Judiciário

## 1. Objetivo do Projeto

Este projeto implementa um **observatório público** para monitorar a **evasão de servidores de Tecnologia da Informação** do poder judiciário federal, com base em **atos administrativos publicados em Diários Oficiais**.

O foco é fornecer **dados agregados, auditáveis e metodologicamente defensáveis**, sem expor dados pessoais, diferenciando claramente servidores de carreira (efetivos) de cargos exclusivamente comissionados.

---

## 2. Conceito de “Evasão” (Definição Oficial do Projeto)

Um evento é considerado **evasão** quando:

- o servidor pertence ao **quadro efetivo** de um órgão do Poder Judiciário, **E**
- exerce função/cargo relacionado à **Tecnologia da Informação**, **E**
- ocorre **saída definitiva do quadro**, **E**
- a saída ocorre por:
  - **Aposentadoria**
  - **Falecimento**
  - **Posse em outro cargo inacumulável** (Evasão para o Executivo, Legislativo ou outros órgãos fora do Judiciário)
  - **Exoneração a pedido**

### ❌ Não é evasão:
- **Exoneração de cargo em comissão** (servidor sem vínculo efetivo).
- Movimentações internas Judiciário → Judiciário (ex: TRT → TRF).
- Redistribuição entre órgãos do mesmo poder.

---

## 3. Classificação e Auditoria

O projeto utiliza um processo de **Auditoria Sistemática** para garantir a qualidade dos dados:

### 3.1 Categorização de Destinos
Para facilitar a visualização e análise, os destinos são agrupados em 3 macro-categorias:
- **falecimento**
- **aposentadoria**
- **outros órgãos** (inclui posse em cargo inacumulável e exoneração)

### 3.2 Ground Truth
Existe uma base auditada manual/sistematicamente (`pipeline/ground_truth.json`) que prevalece sobre a detecção automática por padrão, garantindo que casos específicos (como falecimentos notórios ou renomeações complexas) sejam computados corretamente.

---

## 4. Arquitetura Geral

```
observatorio-evasao-ti/
├── site/               # Dashboard React (Vite)
│   ├── public/data/    # JSONs agregados (series, orgaos, destinos)
│   └── src/            # Componentes e gráficos (ECharts)
├── pipeline/           # Scripts de processamento
│   ├── rules.yaml      # Regras de negócio e termos de TI
│   ├── detect_events.py
│   ├── build_aggregates.py
│   └── run.py          # Execução completa do pipeline
└── brain/              # Documentação estratégica e auditoria
```

---

## 5. Pipeline de Dados

O observatório combina dados do **DOU (2019-2024)** via BigQuery e dados recentes do **DEJT (PDFs)**.

### 5.1 Fluxo de Processamento
1. **Extração**: Coleta de textos dos diários oficiais.
2. **Filtragem**: Seleção de atos relacionados a TI e cargos efetivos.
3. **Detecção**: Aplicação de regras de expressões regulares e NLP.
4. **Auditoria**: Cruzamento com o `ground_truth.json` (CLAUDIO SANTANA, JOYCE QUEIROZ, etc).
5. **Agregação**: Geração de estatísticas por órgão (`orgao`) e mês.

---

## 6. Dados Publicados (LGPD-safe)

O site publica apenas dados agregados e anonimizados:
- `series_mensal.json`: Volumes por mês.
- `top_trts.json`: Ranking de evasão por órgão (identificado como `trt1`, `trt23`, etc).
- `top_destinos.json`: Distribuição por categoria de saída.

---

## 7. Interface e Visualização

O dashboard oferece:
- **Gráficos Interativos**: Implementados com ECharts.
- **Scroll Inteligente**: Gráficos de barras com scroll por mouse/touch (Y-axis) e X-axis fixo.
- **Design Responsivo**: Glassmorphism e tema moderno.

---

## 8. Execução Local

```bash
# Pipeline de Dados
cd pipeline
pip install -r requirements.txt
python run.py

# Dashboard
cd site
npm install
npm run dev
```

---

## 9. Metodologia e Transparência

- **Exclusão de Comissionados**: Foco total na perda de capital intelectual estável.
- **Regras Explícitas**: Lógica baseada no `rules.yaml`.
- **Auditoria Aberta**: Processo documentado de revisão de casos.

---

## 10. Licença

Projeto de interesse público, focado em transparência e gestão de dados governamentais.
