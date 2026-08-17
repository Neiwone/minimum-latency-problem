# H10 — Dynasearch (DP sobre T/C/Cr para combinar 2-opts simultâneos)

Status: **encerrada no diagnóstico. A premissa mecânica é real (não-aditividade
confirmada, diferente do TSP clássico), mas a oportunidade prática de melhoria
é rara e minúscula demais pra justificar construir a DP completa.**

## 1. Motivação e pesquisa

Pesquisa sobre como reaproveitar T/C/Cr (as tabelas de subsequência já usadas
pra avaliar movimentos em O(1) — `include/solution.h`, `src/solution.cpp`)
além da avaliação de um único movimento por vez. Levou a **dynasearch**
(Potts & van de Velde, 1995; Congram, Potts & van de Velde, 2002): uma DP que
busca, em tempo polinomial, a **combinação ótima de movimentos disjuntos
simultâneos** em vez de aplicar um de cada vez — não encontramos essa técnica
combinada com a formalização T/C/Cr de latência acumulada na literatura de MLP,
parece ser uma combinação nova pra este problema.

O motivo de achar isso plausível especificamente para MLP (e não só "mais uma
forma de fazer 2-opt"): como o custo é a soma de latências acumuladas, um
2-opt isolado pode não melhorar por causa do deslocamento de tempo que
introduz em tudo que vem depois dele na rota — mas **dois 2-opts em posições
certas poderiam se cancelar** nesse efeito, mesmo que nenhum dos dois melhore
sozinho. Isso não pode acontecer no TSP clássico (custo = soma de arestas,
puramente aditivo entre movimentos disjuntos — é por isso que dynasearch
"tradicional" só precisa de um valor escalar por posição na DP).

## 2. Complicação técnica encontrada durante o design (antes de codar)

A formulação ingênua de dynasearch (um único valor ótimo por posição da rota)
**não é válida para MLP**: como o custo acumulado depende do tempo `t`
percorrido até aquele ponto, e `t` em si depende de quais reversões foram
escolhidas antes (via as arestas de fronteira, que mudam conforme a
orientação exposta), o estado da DP precisaria ser uma **fronteira de Pareto
em (t, custo)** por posição, não um escalar — bem mais caro de implementar
corretamente do que o dynasearch clássico. Antes de investir nisso, valia
testar a premissa central com algo mais simples e honesto.

## 3. Diagnóstico (read-only, não altera `solution.cpp`/`neighborhoods.cpp`)

Implementado em [`src/diag_dynasearch.cpp`](../../src/diag_dynasearch.cpp)
(compilado à parte, fora do `Makefile`, mesma convenção de
`diag_multi_improvement.cpp`). Método:

1. A partir de um ótimo local convergido por RVND (onde, por definição,
   nenhum 2-opt isolado melhora), calcular o delta exato de **todos** os
   O(n²) candidatos de 2-opt em O(1) cada (via as próprias tabelas T/C/Cr —
   `delta_2opt()` espelha `Solution::evaluate2Opt` mas retorna o delta
   assinado em vez de um booleano).
2. Selecionar os `K` candidatos mais próximos de empatar (menor delta —
   "near-miss").
3. Para cada par disjunto entre esses `K`, aplicar **as duas** reversões de
   verdade numa cópia descartável da rota e recalcular o custo total exato
   direto em O(n) (soma cumulativa de latência, sem precisar reconstruir as
   tabelas O(n²) — só o escalar final importa aqui).
4. Comparar `custo_combinado` contra `custo_base` e também contra
   `delta_A + delta_B` (a soma "aditiva ingênua") — a diferença entre os dois
   é a métrica direta de não-aditividade/sinergia que estamos testando.

Sem aproximação de fronteira: como o custo combinado é recalculado de
verdade a cada par testado, não há o bug de "borda de footprint" encontrado
em H4 (ali a avaliação O(1) de cada movimento lia a posição vizinha
assumindo que ela não mudava; aqui simplesmente aplicamos e recalculamos).

## 4. Resultado

`./bin/diag_dynasearch <instância> --pool 150 --trials 8`, 3 instâncias
grandes (`lin318`/`pr439`/`att532`), 8 ótimos locais cada,
`C(150,2)≈11.175` pares testados por ótimo local (~86 mil pares por
instância, ~258 mil no total):

```
instância   pares testados   melhorando   %melhorando   não-aditivos   %não-aditivo   melhor delta combinado
lin318            85.791            2       0,0023%           1.047        1,22%              -7.082 (-0,114%)
pr439              86.001            1       0,0012%             827        0,96%             -22.663 (-0,118%)
att532             86.738            0       0,0000%             780        0,90%                   0
```

**A não-aditividade é real e consistente** (~0,9-1,2% dos pares testados têm
`custo_combinado ≠ delta_A + delta_B` — confirma a premissa mecânica: MLP
não é como o TSP clássico, combinar dois 2-opts disjuntos pode de fato gerar
sinergia). Mas a magnitude típica dessa sinergia é minúscula (`mean_interaction`
na ordem de poucas unidades, com custos totais na casa dos milhões) e **quase
nunca é grande ou favorável o suficiente pra virar uma melhoria real**: em
~258 mil pares testados (24 ótimos locais no total), só **3 melhorias**
foram encontradas, cada uma em apenas 1 dos 8 ótimos locais por instância
(12,5% de acerto), com ganho de ~0,11-0,12% quando acontece — real, mas
pequeno, e raro.

## 5. Interpretação

A hipótese estava mecanicamente correta (RVND é local-ótimo por definição só
em relação a movimentos *individuais*; a não-aditividade do MLP realmente
abre uma fresta que o TSP clássico não tem), mas a fresta é estreita demais
pra ser um alvo produtivo nesta escala de instância. Mesmo padrão de H5 (o
sintoma diagnosticado é real, mas pequeno demais/raro demais pra virar
ganho prático) — só que aqui a causa raiz é mais fundamental: interação
real entre movimentos existe, só não é grande o bastante.

**Ressalva honesta**: este diagnóstico testa só *pares*, dentro de um pool
de 150 candidatos "quase-melhorando" — um proxy razoável, mas não equivale à
DP completa (que buscaria sobre todas as combinações possíveis, incluindo
3+ reversões simultâneas, não só as top-150 mais próximas de melhorar
individualmente). É possível que a DP completa encontrasse mais oportunidades
que este teste amostrado. Mas dado que a taxa de acerto já é ~0,001-0,002%
com uma amostra generosa (150² pares, 24 ótimos locais), a magnitude do ganho
quando ocorre é pequena (~0,1%), e o padrão da sessão inteira mostra o RVND
absorvendo qualquer vantagem de ponto de partida — não parece que valha o
custo de engenharia de resolver a complicação de fronteira de Pareto (seção 2)
só pra confirmar um efeito desta escala.

## 6. Recomendação

Não implementar a DP completa de dynasearch. **Encerrada definitivamente**
— terceira hipótese consecutiva (depois de H9/H9b/H9c) onde uma ideia bem
fundamentada teoricamente não sobrevive ao teste empírico nesta escala de
instância. A extensão óbvia (repetir em `n≳1000` pra ver se a fresta cresce)
foi considerada e descartada por decisão explícita — não vale mais tempo de
sessão nesta linha; próxima hipótese é H11.
