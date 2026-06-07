# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

## Objetivo

Você deve entregar um software capaz de:

1. **Fazer pull de prompts** do LangSmith Prompt Hub contendo prompts de baixa qualidade
2. **Refatorar e otimizar** esses prompts usando técnicas avançadas de Prompt Engineering
3. **Fazer push dos prompts otimizados** de volta ao LangSmith
4. **Avaliar a qualidade** através de métricas customizadas (Helpfulness, Correctness, F1-Score, Clarity, Precision)
5. **Atingir pontuação mínima** de 0.9 (90%) em todas as métricas de avaliação

---

## Exemplo no CLI

**Exemplo de prompt RUIM (v1) — apenas ilustrativo, para você entender o ponto de partida:**

```
==================================================
Prompt: {seu_username}/bug_to_user_story_v1
==================================================

Métricas Derivadas:
  - Helpfulness: 0.45 ✗
  - Correctness: 0.52 ✗

Métricas Base:
  - F1-Score: 0.48 ✗
  - Clarity: 0.50 ✗
  - Precision: 0.46 ✗

❌ STATUS: REPROVADO
⚠️  Métricas abaixo de 0.9: helpfulness, correctness, f1_score, clarity, precision
```

**Exemplo de prompt OTIMIZADO (v2) — seu objetivo é chegar aqui:**

```bash
# Após refatorar os prompts e fazer push
python src/push_prompts.py

# Executar avaliação
python src/evaluate.py

Executando avaliação dos prompts...
==================================================
Prompt: {seu_username}/bug_to_user_story_v2
==================================================

Métricas Derivadas:
  - Helpfulness: 0.94 ✓
  - Correctness: 0.96 ✓

Métricas Base:
  - F1-Score: 0.93 ✓
  - Clarity: 0.95 ✓
  - Precision: 0.92 ✓

✅ STATUS: APROVADO - Todas as métricas >= 0.9
```
---

## Tecnologias obrigatórias

- **Linguagem:** Python 3.9+
- **Framework:** LangChain
- **Plataforma de avaliação:** LangSmith
- **Gestão de prompts:** LangSmith Prompt Hub
- **Formato de prompts:** YAML

---

## A) Técnicas Aplicadas (Fase 2)

O prompt `prompts/bug_to_user_story_v2.yml` foi refatorado combinando 4 técnicas
complementares de Prompt Engineering. A escolha foi guiada por como
`src/metrics.py` pontua cada métrica:

- **Precision** entra em 3 das 5 métricas (precision, helpfulness, correctness),
  então o prompt precisa **proibir alucinações** explicitamente.
- **Recall** (componente do F1) só sobe se a saída **cobrir todos os aspectos**
  da referência — isso depende da complexidade do bug.
- **Clarity** premia estrutura clara e linguagem direta.

### Técnica 1 — Role Prompting

**O que é:** Definir uma persona detalhada e contexto profissional para o modelo.

**Por que escolhi:** A tarefa exige julgamento de PM sênior (extrair ator,
benefício, agrupar problemas). Sem persona, o modelo escreve user stories
genéricas que tendem a derrubar **Clarity** e **Precision**.

**Como apliquei (trecho do system prompt):**

> "Você é uma Product Manager sênior com mais de 10 anos de experiência em
> refinamento de backlog em times ágeis (Scrum/Kanban). Sua especialidade é
> transformar relatos de bugs — muitas vezes vagos, técnicos ou desorganizados —
> em User Stories de altíssima qualidade..."

### Técnica 2 — Few-shot Learning (obrigatória)

**O que é:** Fornecer exemplos de entrada/saída para que o modelo aprenda o
formato esperado por imitação.

**Por que escolhi:** O dataset tem 3 níveis de complexidade (simples / médio /
complexo) e cada um exige uma estrutura de saída diferente. Few-shot com **um
exemplo de cada nível** ancora o formato e melhora drasticamente **F1-Score**
(Recall sobe ao reproduzir as seções esperadas).

**Como apliquei:** Três exemplos completos no system prompt, todos **sintéticos**
(não copiados do dataset) para evitar data leakage:

- Exemplo 1 — bug simples (filtro de preço): user story + 5 critérios Given/When/Then.
- Exemplo 2 — bug médio (login OAuth intermitente): user story + critérios + `Contexto Técnico`.
- Exemplo 3 — bug complexo (player de vídeo com 3 problemas): seções `=== USER
  STORY PRINCIPAL ===`, `=== CRITÉRIOS DE ACEITAÇÃO ===` agrupados (A/B/C),
  `=== CRITÉRIOS TÉCNICOS ===`, `=== CONTEXTO DO BUG ===`, `=== TASKS TÉCNICAS
  SUGERIDAS ===` e `=== MÉTRICAS DE SUCESSO ===`.

### Técnica 3 — Chain of Thought (CoT)

**O que é:** Instruir o modelo a raciocinar passo a passo antes de produzir a
saída final.

**Por que escolhi:** Analisar um bug envolve várias decisões (identificar ator,
ação, benefício, complexidade, listar detalhes técnicos). Sem CoT, o modelo
pula etapas e produz user stories rasas — derruba **Recall** (e portanto F1).
Mantenho o raciocínio **interno** (regra R7) para não poluir o output e
preservar **Clarity**.

**Como apliquei:** Seção "PROCESSO DE RACIOCÍNIO (Chain of Thought)" com 4
passos numerados: Diagnóstico → Classificação de complexidade → Escolha do
esqueleto → Preenchimento e revisão. Combinada com a regra:

> "R7. Sem raciocínio na saída: NÃO inclua texto como 'Vou analisar...',
> 'Passo 1:', 'Pensando passo a passo:'. A saída é apenas a user story final."

### Técnica 4 — Skeleton of Thought

**O que é:** Fornecer **esqueletos** (templates estruturados) que o modelo
preenche, em vez de inventar a estrutura.

**Por que escolhi:** A maior fonte de perda de **Recall** em bugs complexos é
omitir seções (`Contexto Técnico`, `Tasks Técnicas`, `Métricas de Sucesso`).
Skeleton elimina esse risco ao listar exatamente o que cada complexidade deve
conter. Também é o que mais ajuda **Clarity**, porque garante seções nomeadas
e ordem consistente.

**Como apliquei:** Três esqueletos prontos no system prompt — `Esqueleto SIMPLES`,
`Esqueleto MÉDIO`, `Esqueleto COMPLEXO` — com placeholders `[ator]`, `[ação]`,
`[benefício]`, `[grupo]`, etc., para o modelo preencher.

### Reforços anti-alucinação (Precision)

Além das 4 técnicas, regras explícitas (R1-R10) e edge cases (E1-E7) cercam
falhas comuns:

- **R6** proíbe inventar tecnologias, números, severidades ou impactos não
  mencionados no relato — alavanca direta de **Precision** e **F1-Precision**.
- **R10** força proporcionalidade: bugs simples não ganham seções de tasks
  técnicas (evita verbosidade que derrubaria **Clarity**); bugs complexos não
  perdem seções obrigatórias (evita perda de **Recall**).
- **E1** trata o "ator ausente" — bug sem ator humano vira "Como o sistema
  de X, eu quero...".

---

## B) Resultados Finais

> **Como preencher esta seção após rodar `python src/evaluate.py`:**
> 1. Copie o link do projeto no LangSmith abaixo.
> 2. Capture screenshots do dashboard mostrando os 5 scores ≥ 0.9.
> 3. Atualize a tabela comparativa com os números observados.

### Dashboard LangSmith

- **Link público do projeto:** `https://smith.langchain.com/projects/<SEU_PROJECT>`
- **Link público do prompt v2:** `https://smith.langchain.com/hub/<seu_username>/bug_to_user_story_v2`

### Screenshots

- `docs/screenshot-v2-metrics.png` — dashboard com as 5 métricas ≥ 0.9.
- `docs/screenshot-trace.png` — tracing de pelo menos 3 exemplos.

### Tabela comparativa v1 vs v2

| Métrica       | v1 (baseline ruim) | v2 (otimizado)  | Threshold | Status v2 |
|---------------|--------------------|-----------------|-----------|-----------|
| Helpfulness   | 0.45               | 0.94 _(a confirmar)_ | ≥ 0.90 | ✅ |
| Correctness   | 0.52               | 0.96 _(a confirmar)_ | ≥ 0.90 | ✅ |
| F1-Score      | 0.48               | 0.93 _(a confirmar)_ | ≥ 0.90 | ✅ |
| Clarity       | 0.50               | 0.95 _(a confirmar)_ | ≥ 0.90 | ✅ |
| Precision     | 0.46               | 0.92 _(a confirmar)_ | ≥ 0.90 | ✅ |
| **Média**     | **0.48**           | **0.94** _(a confirmar)_ | ≥ 0.90 | ✅ |

> Os números da coluna v2 são o **alvo** projetado a partir da análise de
> `src/metrics.py`. Substitua pelos valores reais após a primeira execução do
> `evaluate.py`. Se alguma métrica ficar < 0.9, veja "Plano de ajuste" abaixo.

### Plano de ajuste se alguma métrica ficar < 0.9

Cada métrica em `metrics.py` é uma média de sub-critérios. Use o reasoning do
LLM-as-judge para diagnosticar:

| Métrica abaixo | Causa provável | Ajuste no `bug_to_user_story_v2.yml` |
|---|---|---|
| **F1-Score** baixo (Recall) | Saída omite seções obrigatórias para bugs médios/complexos | Reforçar `R10` ("proporcionalidade") e adicionar mais um exemplo médio no Few-shot |
| **F1-Score** baixo (Precision) | Saída inventa tecnologias/números | Reforçar `R6` ("sem invenção"), citá-la novamente perto do final do prompt |
| **Clarity** baixo (Organização / Concisão) | Saída desorganizada ou verbosa | Restringir contagem de critérios em `R9` e endurecer a regra "sem cabeçalhos extras" |
| **Clarity** baixo (Ambiguidade) | Critérios vagos ("deve funcionar bem") | Adicionar instrução: "Critérios devem ser observáveis/testáveis" |
| **Precision** baixo (Alucinação) | Modelo enche lacunas com suposições | Adicionar exemplo de Few-shot com bug vago para mostrar omissão correta |
| **Precision** baixo (Foco) | Saída traz comentários ou introdução | Reforçar `R7` e `R8` ("sem saudações, sem cabeçalhos extras") |

Pequenas variações também ajudam (`LLM_MODEL=gpt-4o` em vez de `gpt-4o-mini`
para a geração; ou `EVAL_MODEL=gpt-4o` para um juiz mais estável).

---

## C) Como Executar

### Pré-requisitos

- Python 3.9+
- Conta no [LangSmith](https://smith.langchain.com/) com `LANGSMITH_API_KEY`
- Pelo menos um provedor de LLM configurado:
  - **OpenAI** (`OPENAI_API_KEY`) — custo estimado ~$1-5 para completar o desafio
  - **Google Gemini** (`GOOGLE_API_KEY`) — free tier (15 req/min, 1500 req/dia)

### 1. Clone e ambiente virtual

```bash
git clone <seu-fork>
cd mba-ia-pull-evaluation-prompt
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credenciais

```bash
cp .env.example .env
# edite .env preenchendo:
#   LANGSMITH_API_KEY=...
#   LANGSMITH_PROJECT=prompt-optimization-challenge-resolved
#   USERNAME_LANGSMITH_HUB=<seu-username-do-langsmith>
#   LLM_PROVIDER=google         (ou openai)
#   GOOGLE_API_KEY=...          (ou OPENAI_API_KEY=...)
```

> Para descobrir seu `USERNAME_LANGSMITH_HUB`: publique qualquer prompt no
> LangSmith Hub, abra-o e clique no ícone de cadeado (🔒).

### 3. Fase 1 — Pull do prompt ruim do LangSmith

```bash
python src/pull_prompts.py
```

Resultado: cria/atualiza `prompts/bug_to_user_story_v1.yml` baixando o prompt
`leonanluppi/bug_to_user_story_v1` do Hub.

### 4. Fase 2 — Refatoração do prompt

Edite `prompts/bug_to_user_story_v2.yml`. Já vem com a versão otimizada deste
projeto (4 técnicas aplicadas). Itere conforme necessário olhando para os
sub-critérios de `src/metrics.py`.

Valide localmente antes de subir:

```bash
pytest tests/test_prompts.py -v
```

Os 6 testes garantem: `system_prompt` não vazio, persona definida, formato
Markdown / template de user story, ≥ 2 exemplos Few-shot, ausência de `[TODO]`
e ≥ 2 técnicas em `techniques_applied`.

### 5. Fase 3 — Push do prompt otimizado para o LangSmith

```bash
python src/push_prompts.py
```

Resultado: publica `{seu_username}/bug_to_user_story_v2` no Hub com tags,
descrição e metadados das técnicas. Tenta marcar como público; se a versão
do `langchain` não suportar, basta tornar público pelo dashboard (botão no
canto superior direito da página do prompt).

### 6. Fase 4 — Avaliação

```bash
python src/evaluate.py
```

> **Atenção a custo:** com OpenAI, esta etapa custa ~$1-5 por execução.
> Com Gemini (`LLM_PROVIDER=google`) é grátis dentro do free tier (15 req/min).

O script:
- Cria/atualiza o dataset `prompt-optimization-challenge-resolved-eval` no LangSmith.
- Faz pull de `{seu_username}/bug_to_user_story_v2` do Hub.
- Executa os 15 exemplos e calcula F1, Clarity, Precision (e deriva Helpfulness
  e Correctness).
- Imprime a tabela final no terminal e cria runs no LangSmith para inspeção.

### 7. Iteração

Espera-se 3-5 iterações para cravar ≥ 0.9 em **todas** as métricas. A cada
rodada:

1. Identifique qual métrica ficou abaixo.
2. Use a tabela em **Plano de ajuste** para escolher a correção no YAML.
3. Faça push novamente: `python src/push_prompts.py`.
4. Re-avalie: `python src/evaluate.py`.

---

## Estrutura do projeto

```
mba-ia-pull-evaluation-prompt/
├── .env.example
├── requirements.txt
├── README.md
│
├── prompts/
│   ├── bug_to_user_story_v1.yml   # Prompt inicial (baseline ruim)
│   └── bug_to_user_story_v2.yml   # Prompt otimizado (Role + Few-shot + CoT + Skeleton)
│
├── datasets/
│   └── bug_to_user_story.jsonl    # 15 exemplos (5 simples, 7 médios, 3 complexos)
│
├── src/
│   ├── pull_prompts.py            # Pull do LangSmith
│   ├── push_prompts.py            # Push ao LangSmith
│   ├── evaluate.py                # Avaliação automática (pronto)
│   ├── metrics.py                 # 5 métricas (pronto)
│   └── utils.py                   # Funções auxiliares (pronto)
│
└── tests/
    └── test_prompts.py            # 6 testes pytest
```

---

## Repositórios úteis

- [Repositório boilerplate do desafio](https://github.com/devfullcycle/mba-ia-prompt-engineering)
- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
