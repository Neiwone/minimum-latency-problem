# H5 — Perturbação guiada por regret de aresta

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Veredito: refutada no diagnóstico.** Em nenhuma das três instâncias (`lin318`,
`pr439`, `att532`) o corte guiado por regret vence o corte aleatório em taxa de acerto e
magnitude ao mesmo tempo; em `pr439` o controle oposto (`inverse_regret`, 62,7% de
acerto) vence com folga e `regret` é o pior dos três. Nada foi implementado em C++.

## Hipótese

Inspirada em Hudson et al. (2022) / GNN-GLS, em que o regret de arestas prevê onde
penalizar em Guided Local Search: enviesar os cortes do double-bridge para as arestas de
maior regret (ponderado pela posição, já que arestas cedo pesam mais no MLP) acharia
escapes de ótimo local mais frequentes ou maiores que cortes aleatórios.

## O que foi testado

`regret(u,v) = dist(u,v) − dist(u, vizinho_mais_próximo_de_u)`, ponderado por posição:
`weighted_regret(p) = regret(tour[p-1],tour[p]) · (n−p)`. Por instância, 5 ótimos
locais de RVND (construção aleatória + `local_search`, sem ILS, o que deixa bastante
folga) e 30 double-bridges por ótimo local para cada estratégia de escolha dos 3 cortes:
`random` (uniforme), `regret` (proporcional a `weighted_regret`) e `inverse_regret`
(proporcional ao inverso, controle). Cada tentativa é reconvergida por
`local_search --route` e comparada ao ótimo local original: 150 tentativas por
estratégia e instância.

## Resultados

| instância | estratégia | hit% | custo médio (delta) | delta médio relativo |
|---|---|---|---|---|
| att532 | random | **75,3** | 38.960 | 0,640% |
| att532 | regret | 72,7 | 32.584 | 0,535% |
| att532 | inverse_regret | 68,7 | **40.261** | **0,662%** |
| lin318 | random | 45,3 | −16.072 | −0,282% |
| lin318 | regret | 42,0 | **−10.892** | **−0,192%** |
| lin318 | inverse_regret | 44,7 | −13.622 | −0,239% |
| pr439 | random | 54,0 | 19.017 | 0,091% |
| pr439 | regret | 53,3 | 7.992 | 0,034% |
| pr439 | inverse_regret | **62,7** | **72.398** | **0,371%** |

Em `att532`, `random` vence `regret` nas duas métricas. Em `lin318` não há vencedor:
`regret` tem o delta menos ruim mas a pior taxa de acerto, e todas pioram em média (uma
única perturbação a partir de um ótimo local fraco, sem ILS, tem alta variância).

## Por que não funcionou

O double-bridge remove a aresta no ponto de corte, mas a reconexão é determinada pela
ordem dos quatro segmentos reorganizados, não pela geometria. Escolher bem onde cortar
(remover uma aresta ruim) não garante que a aresta que entra seja melhor, porque o
double-bridge não escolhe a reconexão por qualidade. O ponto de corte é a alavanca
errada para usar o regret; ele teria efeito num operador que também controla a
reconexão, como um destroy-and-repair no estilo ALNS (remover arestas de alto regret e
reinserir de forma geometricamente gulosa). É também como o GNN-GLS usa o regret: como
penalidade dentro de um Guided Local Search (2-opt/or-opt penalizados), não para escolher
os cortes de um kick estrutural. Esse operador destroy-and-repair não foi testado aqui.

## Limitações

- Diagnóstico com ótimos locais de RVND puro, sem o laço de ILS do GILS-RVND.
- Só três instâncias, entre n=318 e n=532.

## Referências

- Hudson et al. (2022) — GNN-GLS (regret de arestas em Guided Local Search).
