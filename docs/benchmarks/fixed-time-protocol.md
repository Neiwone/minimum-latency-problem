# Protocolo de comparação com tempo fixo (`--max-time`)

**Resumo:** todo solver recebe o mesmo orçamento de wall-clock por execução
(`--max-time`, passado por `run_experiments.py --mode fixed-time --time-limit`), as
execuções rodam uma por vez e são pareadas por seed, e o primeiro solver da lista é o
baseline, com `mean_rel%`, W/T/L e teste de sinal exato por instância e agregado. É o
protocolo de todos os resultados principais em docs/ ([H16](../hypotheses/h16-candidate-neighborhoods.md),
[H19](../hypotheses/h19-dlb-fast-regime.md), [tabelas de resultados](../results-tables.md)),
com 100 s por execução. Duas regras são obrigatórias: execução sequencial e um
orçamento que caiba vários restarts.

## Motivação

Comparar `gils_rvnd`, `gils_am_rvnd` e `mdm_gils_rvnd` com o mesmo `--imax/--iils`
compara orçamentos computacionais diferentes: o custo por iteração varia muito entre
eles (`extended-oropt` varre mais vizinhanças; o `mdm` roda o FPMax* sobre o elite
set). Os resultados de iterações fixas (`salehipour-*.md`) reportam qualidade e tempo
lado a lado, mas não respondem "quem é melhor com o mesmo tempo de CPU?". É a mesma
comparação que o paper do MDM-GILS-RVND faz (arXiv:1908.10705, Seção 5.3.3, "running
time as stopping criterion").

## O que foi implementado

`--max-time SEGUNDOS` nos três binários (`gils_rvnd`, `gils_am_rvnd`,
`mdm_gils_rvnd`):

- O tempo é verificado entre iterações de ILS e entre restarts, nunca no meio de uma
  convergência do RVND: o orçamento pode ser estourado por no máximo uma convergência
  (mais uma mineração, no `mdm`).
- Com `--max-time` e sem `--imax` explícito, `I_max` fica ilimitado, para o tempo ser a
  restrição que manda.
- A saída ganhou `MAX_TIME_S`, `RESTARTS` e, no `mdm`, `MINING_CALLS` /
  `PATTERN_RESTARTS`.

**Correções de fidelidade no `mdm`.** Sob tempo fixo, a divisão de fases do MDM não
pode ser por contagem de restarts: o Algoritmo 4 do paper divide `I_max` em metades
(a primeira constrói o elite set, a segunda minera), e com o tempo mandando a troca
passou a ser na metade do orçamento de tempo. Além disso, o paper chama
`UpdateEliteSet(D, d, s)` dentro do laço de ILS (linhas 8 e 31), e a implementação só
adicionava ao elite set no fim de cada restart. Sem essas correções, orçamentos curtos
tinham `MINING_CALLS 0`: o mecanismo desligado em silêncio, a mesma classe de bug de
[salehipour-n1000-mdm-vs-am-extended](salehipour-n1000-mdm-vs-am-extended.md).

**Estouro de orçamento do `mdm`, resolvido.** A mineração rodava como subprocesso
Python (`scripts/fpmax_mine.py`, não interrompível), e um run de `att532` com
orçamento de 15 s levava 69,6 s de parede: o `mdm` recebia 4,6× mais tempo que os
concorrentes. Com a mineração trocada pela biblioteca C++ FPmax-LIB, chamada em
memória ([H13](../hypotheses/h13-mdm-gils-rvnd.md)), o mesmo caso leva 15,0 s / 15,1 s em duas seeds.

## Regras do protocolo

**1. Execução sequencial, obrigatoriamente.** Comparação de tempo não sobrevive a
contenção de CPU: rodar 6 solvers simultaneamente em 6 núcleos inflou os tempos por
execução em 2-5× com variância enorme (ver
[salehipour-tsplib-mdm-vs-am-extended](salehipour-tsplib-mdm-vs-am-extended.md)). O
modo roda um processo por vez, sempre.

**2. O orçamento precisa caber vários restarts.** O `mdm_gils_rvnd` (mineração) e o
`gils_am_rvnd` (construção por memória adaptativa) só agem em fronteira de restart: o
`mdm` troca de fase na metade do orçamento e precisa de um restart posterior para usar
os padrões; o `gils_am_rvnd` precisa de um elite pool, que só enche depois do primeiro
restart. Com orçamento curto os dois degeneram para GILS-RVND puro, e o "nulo" que
isso produz é sobre o protocolo, não sobre o algoritmo. Medido em `lin318` com 20 s:

| `--iils` | RESTARTS | MINING_CALLS | interpretável? |
|---:|---:|---:|---|
| 100 (default) | 2 | **0** | **não** — mineração nunca disparou |
| 10 | 13 | 4 | sim |

Por isso o modo usa `--iils 10` por padrão para todo solver que não fixa o seu, e
registra `RESTARTS`/`MINING_CALLS` em toda execução, sinalizando os runs em que a
mineração nunca disparou ou houve só 0–1 restart, em vez de reportar um nulo enganoso.

Um piloto (2 instâncias, 15 s, 2 seeds) só verificou a mecânica ponta a ponta.

## Uso — `run_experiments.py --mode fixed-time`

Aceita vários solvers (o primeiro é a referência das comparações pareadas) e o
orçamento em segundos via `--time-limit`:

```bash
# TSPLIB (lista padrão do projeto), 60s por execução, 10 seeds
python3 scripts/run_experiments.py --mode fixed-time --time-limit 60 --runs 10 \
    --solvers gils_rvnd gils_am_rvnd_extended_oropt mdm_gils_rvnd

# instâncias escolhidas a dedo
python3 scripts/run_experiments.py --mode fixed-time --time-limit 60 --runs 10 \
    --instances lin318 pr439 att532 \
    --solvers gils_rvnd gils_am_rvnd_extended_oropt mdm_gils_rvnd

# tiers inteiros do benchmark Salehipour (20 instâncias cada)
python3 scripts/run_experiments.py --mode fixed-time --time-limit 120 --runs 5 \
    --salehipour-sizes 500 1000 \
    --solvers gils_rvnd gils_am_rvnd_extended_oropt mdm_gils_rvnd

# incluindo o or-opt adaptativo (H15)
python3 scripts/run_experiments.py --mode fixed-time --time-limit 60 --runs 10 \
    --instances lin318 att532 \
    --solvers gils_rvnd gils_am_rvnd_extended_oropt gils_am_rvnd_adaptive_oropt mdm_gils_rvnd
```

Parâmetros relevantes: `--time-limit` (segundos, obrigatório), `--iils` (padrão 10,
ver regra 2), `--runs` (seeds, pareadas entre solvers), `--instances` /
`--salehipour-sizes`, `--checkpoint`.

Sem `--checkpoint`, cada lote vai para um arquivo novo com data e hora em
`results/fixed-time/` (o caminho é impresso no início), e nenhum arquivo existente
é sobrescrito. Com `--checkpoint`, o lote retoma daquele arquivo. O checkpoint
guarda a configuração do lote (`--closed` e o comando exato de cada solver,
incluindo `--max-time` e `--iils`), e uma retomada com configuração diferente é
recusada. Acrescentar solvers, instâncias ou seeds a um lote existente é permitido.
`--checkpoint last` retoma o checkpoint mais recente do modo.

Durante o lote, num terminal, Ctrl+P pausa e retoma, e Ctrl+Q para e mostra o
relatório das execuções feitas até ali. A execução em andamento quando qualquer das
duas teclas é pressionada é descartada e refeita do zero, então nenhuma execução salva
inclui tempo de pausa.

**Só aceita solvers cujo binário implementa `--max-time`** (`gils_rvnd`,
`gils_am_rvnd`, `mdm_gils_rvnd` e suas variantes de flag). A verificação é explícita
porque os parsers dos outros binários ignoram flags desconhecidas em silêncio: passar
`--max-time` a eles daria uma comparação que parece certa e roda com orçamento de
iteração ilimitado.

O relatório final traz `mean_rel%`, W/T/L pareado por seed e p-valor do teste de
sinal exato por instância e agregado, mais o bloco de sanidade do protocolo (restarts
médio/mínimo por solver e minerações do `mdm`).

## Limitações

- O orçamento pode ser estourado por uma convergência do RVND (mais uma mineração, no
  `mdm`), porque o tempo não é verificado dentro dela.
- `--iils 10` é um único valor para todos os solvers que não fixam o seu; não é o
  ótimo de cada algoritmo (o [H19](../hypotheses/h19-dlb-fast-regime.md) retuna o `I_ILS` do
  proposto).

## Referências

- MDM-GILS-RVND: arXiv:1908.10705, Seção 5.3.3 ("running time as stopping criterion").
  https://arxiv.org/abs/1908.10705
