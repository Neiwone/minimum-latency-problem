# H5 — Perturbação guiada por regret de aresta

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

Status: **ENCERRADA no diagnóstico — sem sustentação para a hipótese,
sinal misto/oposto em algumas instâncias.** Nenhuma implementação em
C++ foi feita (o diagnóstico bastou para decidir não avançar).

## 1. Hipótese

Inspirada em Hudson et al. (2022) / GNN-GLS (regret de arestas prevendo
onde penalizar/perturbar em Guided Local Search): se cada aresta tem um
"regret" (o quanto pior ela é comparada à melhor alternativa geométrica
disponível), então enviesar os pontos de corte do double-bridge para as
posições de maior regret (ponderado pela posição na rota, já que arestas
cedo importam mais no MLP) deveria encontrar escapes de ótimo local mais
frequentes/maiores do que cortes aleatórios.

## 2. Diagnóstico (sem implementar nada em C++)

Métrica: `regret(u,v) = dist(u,v) - dist(u, vizinho_mais_próximo_de_u)`,
ponderada por posição: `weighted_regret(p) = regret(tour[p-1],tour[p]) * (n-p)`.

Para cada instância: 5 ótimos locais de RVND (construção aleatória +
`local_search`, sem laço de ILS — dá bastante folga de otimização, um
cenário favorável para observar diferenças). Para cada ótimo local, 30
tentativas de double-bridge por estratégia de escolha dos 3 cortes:

- `random`: uniforme (baseline).
- `regret`: probabilidade proporcional a `weighted_regret`.
- `inverse_regret`: probabilidade proporcional ao inverso (controle —
  targeting deliberadamente as posições de *menor* regret).

Cada tentativa é reconvergida via `./bin/local_search --route` e comparada
ao custo do ótimo local original. Script:
`scripts/h5_regret_perturbation_test.py`,
dados: `scripts/h5_regret_results.json`. Instâncias: `lin318`, `pr439`,
`att532` (450 tentativas por instância, 150 por estratégia).

## 3. Resultado

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

Nenhuma instância mostra `regret` vencendo `random` nas duas métricas
(taxa de acerto e magnitude) ao mesmo tempo:

- **`att532`**: `random` vence `regret` nas duas métricas.
- **`lin318`**: sem vencedor claro — `regret` tem o delta médio "menos
  ruim", mas a pior taxa de acerto; todas as estratégias pioram em média
  (esperado — uma única tentativa de perturbação a partir de um ótimo
  local fraco de RVND puro, sem laço de ILS, tem alta variância).
- **`pr439`**: `inverse_regret` — o oposto da hipótese — vence claramente
  nas duas métricas, e `regret` é a pior estratégia das três.

## 4. Interpretação

A hipótese não se sustenta nem no diagnóstico mais barato possível. Uma
explicação mecânica provável: o double-bridge remove a aresta no ponto de
corte, mas a **reconexão é determinada pela ordem dos segmentos
reorganizados, não por proximidade geométrica** — escolher bem *onde*
cortar (remover uma aresta "ruim") não garante que a aresta que a substitui
seja melhor, porque o double-bridge não escolhe a reconexão por qualidade,
só por posição relativa dos 4 segmentos. Ou seja, controlar o ponto de
corte é a alavanca errada para explorar informação de regret — teria efeito
se o mecanismo também controlasse a reconexão (algo mais parecido com um
operador destroy-and-repair estilo ALNS, que remove uma aresta ruim e
depois *reinsere* geometricamente informado, não um double-bridge).

Isso é consistente com como o GNN-GLS de verdade funciona: regret prediz
penalidades usadas dentro de um **Guided Local Search** (2-opt/Or-opt
padrão penalizado), não para escolher pontos de corte de um kick
estrutural como o double-bridge.

## 5. Recomendação

**Não implementar** a versão testada (viés de corte por regret no
double-bridge) em C++ — o diagnóstico já mostra sinal misto/contrário
mesmo no cenário mais favorável (ótimos locais fracos, muita folga). Se
ainda houver interesse na ideia de "regret" como sinal, a forma que teria
chance real precisaria ser um operador diferente — remoção de arestas de
alto regret seguida de reinserção geometricamente gulosa (destroy-and-
repair), não um viés de corte de double-bridge — o que é um lift bem
maior e não foi testado aqui.
