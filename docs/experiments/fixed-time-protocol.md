# Protocolo de comparação com tempo fixo (`--max-time`)

Status: **infraestrutura pronta e validada num piloto curto.** Ainda sem lote
grande. Substitui a comparação "mesmo número de iterações", que é injusta
entre estes algoritmos.

## 1. Por que tempo fixo

Comparar `gils_rvnd`, `gils_am_rvnd` e `mdm_gils_rvnd` com o mesmo
`--imax/--iils` compara **orçamentos computacionais diferentes**: o custo por
iteração é muito diferente entre eles (`extended-oropt` varre mais
vizinhanças; `mdm` roda o FPMax* sobre o elite set). Todos os resultados
anteriores deste projeto (`docs/experiments/salehipour-*.md`) são de
iterações fixas, e por isso reportam qualidade **e** tempo lado a lado — mas
não respondem "quem é melhor com o mesmo tempo de CPU?".

É a mesma comparação que o próprio paper do MDM-GILS-RVND faz
(arXiv:1908.10705, Seção 5.3.3, "running time as stopping criterion").

## 2. Implementação

`--max-time SEGUNDOS` foi adicionado aos três binários (`gils_rvnd`,
`gils_am_rvnd`, `mdm_gils_rvnd`):

- Verificação entre iterações de ILS e entre restarts, **nunca no meio de
  uma convergência do RVND** — o orçamento pode ser estourado por no máximo
  uma convergência (mais o custo de uma mineração, no caso do `mdm`; ver
  seção 4).
- Quando `--max-time` é dado e `--imax` não é passado explicitamente,
  `I_max` vira efetivamente ilimitado, pro tempo ser a restrição que manda.
- A saída ganhou `MAX_TIME_S`, `RESTARTS` e (no `mdm`) `MINING_CALLS` /
  `PATTERN_RESTARTS`.

**Correção de fidelidade no `mdm` feita neste trabalho**: sob tempo fixo, a
divisão de fases do MDM **não pode** ser por contagem de restarts. O
Algoritmo 4 do paper divide `I_max` em metades (primeira metade constrói o
elite set, segunda metade minera); com o tempo mandando, a troca passou a
ser **na metade do orçamento de tempo**, que é a tradução fiel da regra.
Além disso, o paper chama `UpdateEliteSet(D, d, s)` **dentro do laço de ILS**
(linhas 8 e 31), e nossa implementação só adicionava ao elite set no fim de
cada restart — desvio corrigido. Sem essa correção, orçamentos curtos
tinham `MINING_CALLS 0` (mecanismo desligado silenciosamente, a mesma classe
de bug de [[salehipour-n1000-mdm-vs-am-extended]] seção 2).

## 3. Dois requisitos do protocolo (aprendidos na prática)

### 3.1 Execução sequencial, obrigatoriamente

Comparação de tempo não sobrevive a contenção de CPU. Rodar 6 solvers
simultaneamente em 6 núcleos inflou os tempos por execução em 2-5x com
variância enorme neste projeto (ver
[[salehipour-tsplib-mdm-vs-am-extended]] seção 2 e as notas de processo do
tier `n=1000`). `scripts/fixed_time_compare.py` roda **um processo por vez**,
sempre — é mais lento em parede, e é o único jeito de o número significar
algo.

### 3.2 O orçamento precisa caber vários restarts

`mdm_gils_rvnd` (fase de mineração) e `gils_am_rvnd` (construção por memória
adaptativa) **só fazem algo interessante em fronteira de restart**: o `mdm`
troca de fase na metade do orçamento e precisa de um restart posterior pra
usar os padrões; o `gils_am_rvnd` precisa de um elite pool que só enche
depois do primeiro restart. Com orçamento curto, os dois **degeneram para
GILS-RVND puro** — e o resultado "nulo" que isso produz não é sobre o
algoritmo, é sobre o protocolo.

Medido em `lin318` com orçamento de 20s:

| `--iils` | RESTARTS | MINING_CALLS | interpretável? |
|---:|---:|---:|---|
| 100 (default) | 2 | **0** | **não** — mineração nunca disparou |
| 10 | 13 | 4 | sim |

Por isso o script usa `--iils 10` por default (o mesmo para todos os
algoritmos, então a comparação segue justa) e **registra
`RESTARTS`/`MINING_CALLS` em toda execução**, sinalizando os runs em que o
mecanismo não disparou em vez de reportar um nulo enganoso.

## 4. Estouro de orçamento do `mdm` — resolvido

**Era** o problema mais sério do protocolo: a mineração rodava como
subprocesso Python (`uv run --with mlxtend ... scripts/fpmax_mine.py`), não
interrompível, e um run de `att532` com orçamento de 15s levava **69,6s** de
parede — ou seja, o `mdm` recebia 4,6x mais tempo que os concorrentes.

Corrigido trocando a mineração pela biblioteca C++ FPmax-LIB, chamada em
memória (ver [[h13-mdm-gils-rvnd]] seção 2.2). Medido depois da troca, mesmo
caso: **15,0s / 15,1s** em duas seeds — orçamento respeitado. O script
continua gravando `time_ms` e `wall_s` de cada execução pra isso seguir
auditável.

## 5. Uso

```bash
# TSPLIB, 60s por execução, 10 seeds
python3 scripts/fixed_time_compare.py \
    --instances lin318 pr439 att532 --time-limit 60 --iils 10 --seeds 10

# benchmark Salehipour, tier n=500, 120s por execução
python3 scripts/fixed_time_compare.py \
    --salehipour 500 --time-limit 120 --iils 10 --seeds 5

# incluindo o or-opt adaptativo (H15)
python3 scripts/fixed_time_compare.py --instances lin318 att532 \
    --time-limit 60 --seeds 10 \
    --solvers gils_rvnd gils_am_rvnd_extended_oropt gils_am_rvnd_adaptive_oropt mdm_gils_rvnd
```

Checkpoint incremental em `scripts/fixed_time_<T>s.json` (dentro do repo,
não em `/tmp` — ver memória `feedback-experiment-rigor`), retomável. O
relatório final sai com `mean_rel%`, W/T/L pareado por seed e p-valor do
teste de sinal exato por instância e agregado, mais o bloco de sanidade do
protocolo.

## 6. Piloto (2 instâncias, 15s, 2 seeds — sem valor estatístico)

```
Sanidade do protocolo:
  gils_rvnd                      restarts medio=   8.5 min=3
  gils_am_rvnd_extended_oropt    restarts medio=   8.5 min=3
  mdm_gils_rvnd                  restarts medio=   5.8 min=2  runs sem mineracao=0/4

--- gils_am_rvnd_extended_oropt vs gils_rvnd ---
instancia               mean_rel%      w/t/l   sign_p
lin318                     -0.305      1/0/1   1.0000
att532                     -0.983      2/0/0   0.5000
AGREGADO                   -0.644      3/0/1   0.6250

--- mdm_gils_rvnd vs gils_rvnd ---
instancia               mean_rel%      w/t/l   sign_p
lin318                     +0.276      0/1/1   1.0000
att532                     +0.236      0/1/1   1.0000
AGREGADO                   +0.256      0/2/2   0.5000
```

Direção coerente com os lotes de iteração fixa (AM+extended-oropt à frente,
`mdm` levemente atrás), mas com N=2 **não afirma nada** — serve só como
verificação de que a mecânica funciona ponta a ponta.

## 7. Escolha do orçamento `T` para o lote de verdade

Recomendação (a combinar): usar como `T` o tempo médio que o `gils_rvnd`
baseline gasta no protocolo padrão do paper naquele tamanho, que é o que os
documentos anteriores já mediram — assim o orçamento é "natural" e os
resultados ficam comparáveis aos lotes de iteração fixa:

| tamanho | tempo médio do baseline (protocolo padrão) | `T` sugerido |
|---|---:|---:|
| `lin318` (n=318) | ~110s | 110s |
| `pr439` (n=439) | ~289s | 290s |
| `att532` (n=532) | ~702s | 700s |
| Salehipour n=500 | ~1105s | 1100s |
| Salehipour n=1000 (`--imax 1`) | ~370s/run | 370s |

Com `--iils 10`, esses orçamentos dão dezenas de restarts, então os dois
mecanismos de fronteira de restart ficam bem exercitados.
