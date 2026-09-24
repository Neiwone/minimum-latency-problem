# H8 — Algoritmo memético populacional (DBMEA-lite)

**Veredito: refutada na escala testada.** Em nenhuma configuração o DBMEA-lite bateu o
GILS-RVND em qualidade, em `lin318`, `att532` e `rand1000` (n=318/532/1000): em
`rand1000` o GILS-RVND fica ~2,7–2,9% melhor. Com os parâmetros do artigo
(`pop-size=100`, `n-transfers=40`) piora ligeiramente em `lin318` (5.671.916 contra
5.659.325). O DBMEA-lite é mais rápido, com vantagem crescendo com `n` (1,4–2,2× menos
tempo em `rand1000`). Não adotado. Todos os números são de calibração, sem seeds
pareadas; a escala de tempo do artigo (horas por execução) não foi testada.

## Hipótese

Depois de H1–H6 mostrarem que nenhuma intervenção pontual em torno do RVND sobrevive a
ele (o RVND leva qualquer ponto de partida, perturbação ou recombinação a qualidade
parecida), um método genuinamente populacional poderia superar o GILS-RVND. O DBMEA
(Tüű-Szabó, Földesi & Kóczy, 2020) reporta exatamente isso em instâncias grandes
(n=500: +0,35%; n=1000: +0,40–0,57% melhor e ~1,9× mais rápido), empatando nas
pequenas e médias. O GQPSO (Jmal, Haddar & Chabchoub, 2025) mostra o mesmo padrão;
o DBMEA foi escolhido por mapear mais diretamente em `Solution`, `RVND` e `construction`.

## O que foi testado

Binário [`src/dbmea.cpp`](../../src/dbmea.cpp), três operadores por geração sobre uma
população de `--pop-size` rotas:

1. **Mutação bacteriana:** percorre cada indivíduo em segmentos de tamanho `--seg-len`
   (padrão `n/20`); para cada segmento gera `--n-clones` clones (padrão `n/15`), um com o
   segmento revertido e os demais embaralhados, e mantém o de menor custo.
2. **Transferência de genes:** ordena a população, divide em metades e copia segmentos
   aleatórios (`--transfer-len`) da metade superior para posições aleatórias da inferior
   (`--n-transfers` vezes), removendo os clientes duplicados.
3. **Passo memético:** RVND nos `--memetic-top-k` indivíduos.

Mutação e transferência só precisam do custo da rota completa, O(n); os indivíduos só
viram `Solution` (com T/C/Cr) para o RVND. Determinístico com `--seed`, rotas sempre
permutações válidas; em `eil51` converge para 9319, o valor que o GILS-RVND encontra.

**Bug de desenho corrigido:** a primeira versão rodava o RVND só nos top-3
(`--memetic-top-k 3`) e travava após a 1ª geração (o melhor custo não mudava de gen=2 a
gen=100). Mutação e transferência são operadores aleatórios muito mais fracos que o RVND:
os top-3 polidos viram ótimos locais que eles nunca superam por sorte, e o resto da
população, sem polimento, nunca chega perto para competir. Com o RVND na população
inteira (padrão agora `popSize`), o melhor custo cai por dezenas de gerações
(`5827K → 5780K → 5696K → 5678K → 5659K` em 100 gerações em `lin318`).

## Resultados

Orçamentos de tempo parecidos, 1 execução por configuração:

| instância | dbmea (custo / tempo) | gils_rvnd (custo / tempo) | resultado |
|---|---|---|---|
| lin318 | 5.659.325 / 43,0s | 5.562.365 / 35,1s | GILS-RVND melhor em qualidade e mais rápido |
| att532 | 5.791.790 / 116,8s | 5.653.489 / 183,1s | GILS-RVND melhor em qualidade; dbmea ~1,6x mais rápido |

Em `rand1000` (gerada com `instance_generator.py --n 1000 --grid 1000 --seed 42`):

| execução | dbmea | gils_rvnd |
|---|---|---|
| mesmo nº de "unidades de esforço" (10 gerações vs imax=1/iils=100) | 10.899.753 / 124,6s | 10.595.879 / 279,0s |
| dbmea com mais gerações (22) buscando orçamento de tempo parecido | 10.891.847 / 204,6s | (mesmo de cima: 10.595.879 / 279,0s) |

Com os parâmetros do artigo em `lin318` (~45–50 s):

| configuração | custo final | tempo |
|---|---|---|
| pop=20, 100 gerações (antes do ajuste) | 5.659.325 | 43,0s |
| pop=100, 30 gerações (parâmetros do paper) | 5.671.916 | 49,5s |

## Por que não funcionou

A população converge cedo e para de explorar: em `rand1000`, passar de 10 para 22
gerações move o custo só 0,07% (10.899.753 → 10.891.847), o mesmo platô de `lin318`. O
platô persiste com `pop=100`, então não é artefato de população pequena. A tempo fixo,
população menor com mais gerações vence a população do artigo com poucas, porque cada
geração com `pop=100` custa ~5× mais (o RVND memético roda em todos). Igualar os
parâmetros do artigo sem igualar sua escala de tempo (~4,2 h por execução em n=1000) não
reproduz o resultado; provavelmente seriam necessárias centenas ou milhares de gerações.
A vantagem de tempo (quase nula em 318, ~1,6× em 532, maior em 1000) segue a tendência
que a literatura reporta, mas sem a vantagem de qualidade; é o mesmo padrão do
GILS-AM-RVND: ganho de tempo, não de qualidade.

## Limitações

- Um ponto de calibração por instância, sem seeds pareadas: não é teste estatístico.
- A escala do artigo (população 100, centenas ou milhares de gerações, horas por
  execução) não foi testada; em `rand1000` cada geração custa ~40 s já com `pop-size=10`.
- `nClones`/`segLen`/`transferLen` ficaram nos valores derivados da fórmula do artigo
  (`n/15`, `n/20`), sem ajuste para este código; o "Circle Group Heuristic" (construção
  inicial mais diversa) não foi implementado.
- Continuam em aberto rodar a escala do artigo ou ajustar os operadores, e o GQPSO.

## Referências

- Tüű-Szabó, B., Földesi, P., Kóczy, L.T. (2020). DBMEA (Discrete Bacterial Memetic
  Evolutionary Algorithm). *International Journal of Computational Intelligence
  Systems*, 13(1), 781–793.
- Jmal, Haddar, Chabchoub (2025). GQPSO (Guided Quantum PSO).
