# H15 — Or-opt com `k_max` adaptativo (`--rvnd-mode adaptive-oropt`)

Status: **implementado e validado funcionalmente; ainda SEM teste estatístico
pareado.** Calibração de 1 seed só (não conclui nada — ver seção 5). O achado
funcional interessante: com os limiares calibrados, a política **redescobre
sozinha `k_max=6` em `lin318`**, exatamente o valor que o [[h12-extended-oropt]]
tinha fixado à mão.

## 1. Motivação

`RVND_ExtendedOrOpt` (H12a, o único ganho real de qualidade do projeto)
fixa os comprimentos de or-opt em 2..6 e sorteia entre eles com
probabilidade uniforme, sempre. Duas coisas ficam na mesa:

1. **O teto útil não é o mesmo em toda instância nem em toda fase da
   busca.** Um `k_max` fixo simultaneamente *paga demais* (varre O(n²) em
   comprimentos que pararam de produzir) e *paga de menos* (nunca tenta
   7..12 quando ainda valeriam).
2. **Dentro do teto, os comprimentos não são igualmente produtivos**, mas
   o RVND clássico os visita com probabilidade uniforme.

## 2. Mecanismo

`src/rvnd_adaptive.cpp` / `include/rvnd_adaptive.h`:

- **Seleção por roleta**: a lista de vizinhanças tem as três estruturas
  fixas (swap, 2-opt, reinserção = or-opt de comprimento 1, peso 1,0) mais
  uma entrada por comprimento de or-opt em [2, `kMax`], cada uma com seu
  **peso aprendido** — os comprimentos que estão produzindo passam a ser
  visitados mais.
- **Crédito**: toda varredura é uma tentativa; varredura que melhora ganha
  `1 + gainScale × (melhoria relativa)`. Recompensa do comprimento =
  crédito/tentativas no período.
- **Adaptação** (a cada `period` varreduras, acumuladas **entre chamadas do
  RVND** — o estado vive na execução inteira, não em uma convergência, senão
  não há amostra pra estimar nada): pesos suavizados na direção da
  recompensa observada, `w ← (1-ρ)·w + ρ·recompensa_normalizada`, com piso
  pra nenhum comprimento morrer de vez; depois o **teto se move** — se a
  fronteira (os maiores comprimentos habilitados) ainda acerta acima de
  `growHitRate`, `kMax` cresce 1 (até `K_CAP=12`, o novo comprimento
  entrando com peso otimista pra ter chance justa); se acerta abaixo de
  `shrinkHitRate`, `kMax` diminui 1 (nunca abaixo de `K_FLOOR=3`).

A terminação é a mesma do `RVND()` original: para quando toda estrutura da
lista falhou, então o resultado continua sendo um ótimo local em relação às
vizinhanças habilitadas.

## 3. CLI

```bash
./bin/gils_am_rvnd <inst> --rvnd-mode adaptive-oropt \
    [--adapt-kstart 6] [--adapt-period 400] [--adapt-rho 0.30] \
    [--adapt-grow 0.10] [--adapt-shrink 0.02] [-v]
```

Também disponível em `./bin/gils_rvnd --rvnd-mode adaptive-oropt`. A saída
inclui `ADAPT_KMAX_FINAL` e `ADAPT_KMAX_RANGE`; com `-v`, o `stderr` recebe
a tabela completa por comprimento (varreduras, acertos, hit rate, ganho
médio, peso final). Os cinco knobs são candidatos naturais pro irace (ver
`irace/`).

## 4. Observações funcionais (1 seed cada — não são resultados)

**Os limiares default (`grow=0.10`) deixam o teto sem função**: em `eil51` e
`lin318` o `kMax` saturou no teto rígido (12), porque a fronteira segue
acertando ~10%. Ou seja, com o default a política vira "or-opt até 12 com
seleção ponderada" em vez de escolher um teto.

Com `--adapt-grow 0.25 --adapt-shrink 0.12` o teto passa a decidir de fato:

| Instância | `--adapt-kstart` | `kMax` final | faixa visitada |
|---|---:|---:|---|
| `lin318` | 6 (default) | **6** | 6..6 |
| `lin318` | 3 | **6** | 3..6 |
| `eil51` | 4 | 7 | 4..10 |
| `rand6` (n=6) | 6 | 3 (piso) | 3..6 |

Em `lin318` a política **converge para `k_max=6` partindo de baixo (3) ou de
cima (6)** — o mesmo valor que o H12a escolheu à mão depois de um
diagnóstico manual. Em instância pequena (`eil51`) ela escolhe um teto mais
alto (7), e em instância minúscula cai pro piso. É o comportamento que se
esperaria de um parâmetro que deveria depender da instância.

**Estatística por comprimento em `lin318`** (`-v`, 1 seed, `--iils 20`): o
hit rate cai com o comprimento (0,42 em L=2 → 0,10 em L=12) mas o **ganho
médio relativo cresce** (0,0147 → 0,0361) — segmentos longos acertam menos e
ganham mais quando acertam. Isso explica por que a fronteira continua
"valendo a pena" pelos critérios de hit rate puro, e é um argumento pra
recompensa ponderada por ganho (que é o que `gainScale` faz).

**Custo/qualidade, 1 seed, `lin318`, `--iils 20`, mesma seed** (spot check,
zero valor estatístico — N=1):

| modo | custo | tempo |
|---|---:|---:|
| `single` | 5.594.734 | 23,6s |
| `extended-oropt` | 5.571.913 | 20,6s |
| `adaptive-oropt` (defaults) | 5.590.970 | 26,7s |
| `adaptive-oropt` (`grow=0.25 shrink=0.12`) | 5.581.227 | — |

## 5. O que falta

**Nada aqui é resultado ainda.** Pelo padrão de rigor já estabelecido no
projeto (memória `feedback-experiment-rigor`): lote pareado por seed,
N≥15-20, em `n≳300` (`lin318`/`pr439`/`att532`), teste de sinal, e checagem
de overhead de tempo. Ordem sugerida:

1. Calibrar `grow`/`shrink`/`period`/`rho` (irace, `irace/` — os knobs já
   estão expostos na CLI justamente pra isso), em instâncias de treino
   separadas das de reporte.
2. Lote pareado `adaptive-oropt` vs `extended-oropt` (o competidor real; o
   `single` já se sabe pior) em `n≳300`.
3. Se sobreviver: repetir em `n=1000` do benchmark Salehipour, onde o efeito
   do H12a é mais forte.

Vale registrar a expectativa honesta: o `extended-oropt` fixo já é forte, e
a maioria das hipóteses deste projeto morreu no lote pareado depois de
parecer boa em 1 seed (H6, H13, o follow-up do `grasp_am`). O caso favorável
aqui é que a política **reencontrou o `k_max=6` do H12a sozinha**, o que
sugere que ela ao menos não destrói o achado — o ganho, se houver, deve vir
de instâncias onde o teto ótimo não é 6.
