# Tipos de distância suportados

O `Evaluator` agora lê os cinco tipos de `EDGE_WEIGHT_TYPE` que aparecem nas
instâncias simétricas do TSPLIB. Antes só `EUC_2D` e `ATT`.

| tipo | fórmula | instâncias aqui |
|---|---|---|
| `EUC_2D` | `(int) sqrt(dx²+dy²)` | 64 |
| `ATT` | `ceil(sqrt((dx²+dy²)/10))` | 2 |
| `CEIL_2D` | `ceil(sqrt(dx²+dy²))` | 2 |
| `GEO` | grande círculo, `RRR = 6378.388` | 5 |
| `EXPLICIT` | matriz no arquivo | 5 |

Dois detalhes que não são óbvios:

- **`EUC_2D` trunca, não arredonda.** O TSPLIB especifica `nint`. Este projeto
  trunca desde o início; manter assim preserva a comparabilidade com todos os
  resultados já registrados. `CEIL_2D` e `GEO` seguem a definição padrão, porque
  não têm histórico aqui.
- **`GEO` precisa de diagonal explícita.** A fórmula do TSPLIB devolve `1` para
  `i == j` (`acos(1) = 0`, e depois soma-se `1.0`). Sem zerar a diagonal, toda
  distância própria vale 1.

`EXPLICIT` cobre `FULL_MATRIX`, `UPPER_ROW`, `UPPER_DIAG_ROW`, `LOWER_ROW` e
`LOWER_DIAG_ROW` — cada formato lista um triângulo diferente, que é lido e
espelhado.

## Verificação

`scripts/verify_tour.py` aprendeu as mesmas três convenções (incluindo o `PI =
3.141592` truncado que o TSPLIB usa em `GEO`) e recalcula a latência do tour
de forma independente do solver.

```
python3 scripts/verify_tour.py instances/si1032.tsp \
    ./bin/gils_am_rvnd instances/si1032.tsp --rvnd-mode candidate-dlb --max-time 5
```

Resultado: 22/22 instâncias com custo reportado igual ao recalculado, cobrindo os
cinco tipos e quatro dos cinco formatos de matriz (`LOWER_ROW` não aparece nas
instâncias simétricas do TSPLIB). As instâncias `EUC_2D`/`ATT` já existentes
continuam com o mesmo resultado.

## Instâncias que exigem 64 bits

Junto de `fnl4461`, estas só funcionam depois da migração descrita em
[cost-64-bit.md](cost-64-bit.md):

| instância | n | custo obtido | vs `INT_MAX` |
|---|---:|---:|---:|
| `dsj1000` | 1000 | 7 863 692 606 | 3,7× |
| `pla7397` | 7397 | 65 344 755 111 | 30× |
