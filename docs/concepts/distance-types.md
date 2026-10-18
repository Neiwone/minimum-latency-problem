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

- **O arredondamento de `EUC_2D` acompanha a variante do problema**, como na
  literatura:

  | variante | convenção | literatura |
  |---|---|---|
  | caminho (padrão) | **trunca**: `(int) √(dx² + dy²)` | Salehipour et al. (2011) ("*rounded down to the nearest integer*"); Silva et al. (2012), Tabela 2; o conjunto de 10 TSPLIB do MDM-GILS-RVND |
  | circuito (`--closed`) | **`nint`** do TSPLIB: `(int)(√(dx² + dy²) + 0,5)` | Abeledo et al. (2010); Bulhões et al. (2018); Silva et al. (2012), Tabela 1; Santana et al. (2019), Tabela 1 |

  A evidência é numérica: no caminho, o projeto reproduz exatamente os BKS
  publicados truncando (`st70` 19 215, `lin318` 5 560 679, `pr439` 17 688 561); no
  circuito, só com `nint` os ótimos provados batem (`pr124` 3 154 346, `kroA150`
  1 825 769; [mdm-paper-table1-reproduction](../benchmarks/mdm-paper-table1-reproduction.md)).
  `--nint` e `--trunc` (em `gils_rvnd`, `gils_am_rvnd` e `mdm_gils_rvnd`) forçam uma
  das duas; os demais binários seguem a mesma regra pelo `Evaluator`, exceto o
  `backtracking`, que só resolve o caminho e trunca. `CEIL_2D` e `GEO` seguem a
  definição padrão do TSPLIB nas duas variantes.
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
