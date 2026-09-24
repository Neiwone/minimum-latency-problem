# Custo em 64 bits

## Motivação

O custo de latência cresce como `Σ (n-q)·d(π_{q-1}, π_q)`: cada aresta é paga por
todos os clientes que ainda faltam. Isso o faz crescer com `n²`, não com `n`, e em
algum ponto ele não cabe mais em `int32`.

O ponto de ruptura observado é `n ≈ 4500`. Em `fnl4461` o solver reportava:

```
int32  FAIL n=4461 reported=-2147483648 recomputed=2147483648
int64  OK   n=4461 reported=392340983   recomputed=392340983
```

O custo verdadeiro do tour que o int32 devolveu é exatamente `2³¹` — e isso não é
coincidência. Em aritmética truncada o menor valor representável é `INT_MIN = -2³¹`,
atingido justamente por custos verdadeiros de `2³¹`. Como a busca **minimiza**, ela
perseguiu os tours que dão wrap para o valor mais negativo possível: o solver não só
reportou lixo, ele otimizou o lixo. A solução resultante é 5,5× pior que a do int64.

Abaixo de `n ≈ 1300` o int32 estava correto. Verificação independente (recálculo do
tour a partir das coordenadas) em `pr1002`, `u1060`, `vm1084`, `rl1304` e `rl1323`:
os 10 tours são válidos e 4 dos 5 pares dão custo idêntico entre as duas versões.
O tour *aleatório* nessas instâncias chega a 6,5e9 (3× o limite do int32), mas a
busca nunca visita esse regime — a construção é gulosa.

## O que mudou

`typedef long long Cost` em `include/solution.h`, propagado por ~90 pontos: os
acumuladores das funções `evaluate*`, os retornos de `getT`/`getC`/`getCr` (que
tinham cast explícito para `int`), os tipos de retorno das `delta_*`,
`full_route_cost` e `tour_cost`, os campos `EliteEntry::cost`, `TabuMove::cost`,
`Candidate::delta` e `DiagResult::bestDelta`, e os sentinelas `INT_MAX → LLONG_MAX`.

Os vetores `P` e `SP` já eram `long long*` — o truncamento estava só nos casts de
retorno e nos acumuladores locais.

Distâncias individuais e posições continuam `int`: elas não acumulam.

## Verificação

- `g++ -Wconversion -fsyntax-only` em todos os `src/*.cpp`: zero truncamentos
  `Cost → int`.
- **Bit a bit**: 36 execuções determinísticas (`--imax 2 --seed {1,2}`) em
  `rat195`, `pr226`, `a280`, `lin318`, `pr439`, `att532`, com `gils_am_rvnd`,
  `mdm_gils_rvnd` e `gils_rvnd`, todas com custo idêntico ao binário anterior.
  A trajetória de busca não mudou onde não havia estouro.

```
for f in src/*.cpp; do g++ -std=c++11 -Iinclude -Wconversion -fsyntax-only "$f"; done
python3 scripts/verify_tour.py instances/fnl4461.tsp \
    ./bin/gils_am_rvnd instances/fnl4461.tsp --rvnd-mode candidate-dlb --max-time 60
```

## Instâncias destravadas

`pr1002`, `u1060`, `vm1084`, `rl1304`, `rl1323` e `fnl4461` entraram em
`instances/`. Só `fnl4461` dependia de fato da migração; as outras cinco estavam
retidas por precaução.
