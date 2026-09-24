# Latência com ou sem volta ao depósito

O MLP é definido sobre um **caminho** hamiltoniano: o custo é a soma dos tempos
de chegada dos clientes, e a volta ao depósito não é paga. A flag `--closed`
troca para a variante fechada, que soma um termo a mais — a chegada de volta ao
depósito.

```
aberto  = Σ_{q=1..n-1} chegada(q)
fechado = aberto + (caminhada total + d(último, depósito))
```

Reescrito por aresta, a diferença é só o peso: no aberto uma aresta na posição
`q` é paga por `n-q` clientes; no fechado, por `n+1-q`, mais a aresta de
fechamento paga uma vez.

## Onde está

| | |
|---|---|
| solvers | `--closed` em `gils_am_rvnd`, `mdm_gils_rvnd`, `gils_rvnd` |
| harness | `--closed` em `run_experiments.py`, em todos os modos |
| visualizador | botão **volta ao depósito: SIM/NÃO** no `edit-route` |

Cada solver imprime `CLOSED 0` ou `CLOSED 1`, para um log nunca ficar ambíguo.

## Como foi implementado

A avaliação O(1) de movimento já monta, por concatenação de subsequências, o
custo aberto `c` da rota candidata, junto com a caminhada total `t` e a última
cidade. O custo fechado é `c + t + d(última, depósito)` — uma linha no fim de
cada uma das seis funções `Solution::evaluate*`, mais os pontos que fixam
`fEvaluationValue`. A busca inteira dos três solvers passa por ali, então o
objetivo muda de verdade: não é só o número reportado no fim.

## Cuidados

- **Os melhores conhecidos em `instances/solutions/` são custos abertos.** No
  modo fechado o `run_experiments.py` suprime o gap contra eles e não grava nada
  por cima — comparar as duas convenções daria um número sem significado.
- **Solvers sem `--closed` falham alto.** Pedir `--closed` para um binário que
  não tem a flag levanta erro em vez de rodar e reportar custo aberto em
  silêncio.
- Um `.tour` salvo pelo editor registra a convenção no `COMMENT`.

## Verificação

Custo reportado contra recálculo independente (`scripts/verify_tour.py` e
`arrival_times`), nos dois modos, nos três solvers, em `rat195`, `gr120` e
`att48`: 9/9 exatos. O modo aberto continua devolvendo os mesmos custos de
antes.

## Otimizar o fechado não compensa

Teste pareado por semente, 12 sementes, `--imax 3`: a rota do modo fechado
contra a rota do modo aberto, ambas medidas na métrica fechada.

| instância | média | V/E/D | p |
|---|---:|---:|---:|
| `pr226` | +0,000% | 0/12/0 | 1,0000 |
| `lin318` | −0,034% | 7/0/5 | 0,7744 |

Empate. Otimizar o objetivo fechado não devolve rota melhor do que otimizar o
aberto e medir fechado — em `pr226`, empate exato nas 12 sementes.

Não é a flag falhando: as rotas de fato mudam e o custo reportado é o fechado.
É que os dois objetivos quase coincidem. O termo extra tem peso `1` por aresta,
contra pesos que vão até `n` no termo de latência, então ele pesa pouco e
encolhe com `n`:

| | att48 | pr226 | lin318 | att532 |
|---|---:|---:|---:|---:|
| termo extra, % do custo fechado | 5,47% | 1,33% | 0,88% | 0,57% |

Ou seja: para reportar o custo fechado, basta rodar no modo aberto e somar
`caminhada + d(último, depósito)`. A flag serve para quem precisa que a busca
seja formalmente coerente com a métrica relatada, não para ganhar qualidade.
