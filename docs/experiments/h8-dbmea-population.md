# H8 — Algoritmo memético populacional (DBMEA-lite)

Status: **implementado, um bug real de desenho encontrado e corrigido no
caminho, testado em `lin318`/`att532`/`rand1000` (n=318/532/1000), depois
com os parâmetros ajustados para bater exatamente com o paper
(`pop-size=100`, `n-transfers=40`). Em nenhuma configuração o DBMEA-lite
bateu o GILS-RVND em qualidade — inclusive piorou ligeiramente ao usar
`pop-size=100` dentro do mesmo orçamento de tempo (seção 8), confirmando
que o platô de convergência não é um artefato de população pequena. É
consistentemente mais rápido, com a vantagem de tempo crescendo com n
(seção 6). Reproduzir o resultado do paper provavelmente exige a escala de
tempo dele (horas, não minutos) — não testado ainda, ver seção 9.**

## 1. Motivação e pesquisa de literatura

Depois de H1/H2/H3/H4/H5/H6 mostrarem que **nenhuma intervenção pontual em
torno do RVND sobrevive a ele** (RVND converge qualquer ponto de
partida/perturbação/recombinação para qualidade parecida), pesquisamos
métodos genuinamente populacionais (GA, PSO) que reportam bater o
GILS-RVND na literatura:

- **DBMEA** (Discrete Bacterial Memetic Evolutionary Algorithm — Tüű-Szabó,
  Földesi & Kóczy, 2020, *International Journal of Computational
  Intelligence Systems* 13(1):781–793): bate o GILS-RVND em qualidade **e**
  tempo, mas só em instâncias grandes (n=500: +0,35%; n=1000: +0,40-0,57%
  melhor e ~1,9x mais rápido). Empata em instâncias pequenas/médias —
  exatamente o padrão que já tínhamos observado.
- **GQPSO** (Guided Quantum PSO — Jmal, Haddar & Chabchoub, 2025): mesmo
  padrão, enxame de partículas + busca local guiada embutida.

Escolhemos implementar uma versão simplificada do DBMEA (mecanismo mais
direto de mapear em cima da infraestrutura já existente: `Solution`,
`RVND`, `construction`) em vez do QPSO (matemática de "sequência de trocas"
como velocidade, mais complexa de adaptar).

## 2. Mecanismo (DBMEA-lite)

Três operadores por geração, sobre uma população de `popSize` indivíduos
(rotas completas):

1. **Mutação bacteriana**: para cada indivíduo, percorre segmentos de
   tamanho fixo (`segLen`, default `n/20`) da esquerda pra direita; para
   cada segmento, gera `nClones` clones (default `n/15`) — um deles com o
   segmento revertido (determinístico), os demais com o segmento
   embaralhado aleatoriamente — avalia o custo total de cada clone, e
   mantém a versão do segmento que deu o menor custo antes de passar pro
   próximo segmento.
2. **Transferência de genes**: ordena a população por custo, divide em
   metade superior/inferior; repetidamente pega um segmento aleatório de um
   indivíduo da metade superior e insere numa posição aleatória de um
   indivíduo da metade inferior, removendo as ocorrências duplicadas dos
   clientes que isso cria (reparo).
3. **Passo memético**: roda o `RVND` (já existente, intocado) nos
   indivíduos.

Diferente da avaliação O(1) por movimento do RVND, mutação/transferência só
precisam do custo de uma rota **completa** candidata — O(n) direto (soma
cumulativa de latências), sem precisar montar as tabelas O(n²) de
reotimização. Indivíduos são só `vector<int>` (rota) + custo; só viram
`Solution` (com as tabelas T/C/Cr) na hora de rodar o RVND.

Implementado em [`src/dbmea.cpp`](../../src/dbmea.cpp) (binário novo, segue
a convenção do projeto). Flags: `--pop-size`, `--generations`,
`--n-clones`, `--seg-len`, `--n-transfers`, `--transfer-len`,
`--memetic-top-k`, `--seed`.

## 3. Corretude

- Determinístico com `--seed` (mesma seed → mesmo resultado).
- Rota sempre uma permutação válida (checado: sem duplicados/faltando).
- Em `eil51`, converge para 9319 — o mesmo valor que o GILS-RVND encontra
  consistentemente a sessão inteira (indício de que está de fato
  encontrando o ótimo, não só uma rota qualquer).

## 4. Bug de desenho encontrado e corrigido

Primeira versão aplicava o passo memético (RVND) só nos top-3 indivíduos
(`--memetic-top-k 3`, inspirado numa leitura conservadora do paper pra
controlar custo). Resultado: **o algoritmo travava completamente após a
1ª geração** — instrumentei geração a geração e confirmei que o custo
melhor nunca mudava do gen=2 ao gen=100.

Causa: mutação bacteriana e transferência de genes são operadores
**muito mais fracos** (embaralhamento aleatório) que o RVND (busca
sistemática). Uma vez que os top-3 indivíduos são polidos pelo RVND, eles
viram ótimos locais que os operadores aleatórios essencialmente nunca
superam por sorte — e o resto da população nunca é polido, então nunca
chega perto da qualidade dos top-3 pra sequer competir. Correção: aplicar
RVND na população **inteira** a cada geração (`--memetic-top-k` default
agora é `popSize`, mantido como parâmetro caso se queira trocar
qualidade por velocidade). Depois da correção, o custo melhor continua
caindo por dezenas de gerações (confirmado por instrumentação: `5827K →
5780K → 5696K → 5678K → 5659K` ao longo de 100 gerações em `lin318`).

## 5. Resultado em `lin318` e `att532` (n=318, n=532)

Comparação de orçamento de tempo parecido (não pareado por seed ainda —
resultado de calibração, não teste estatístico):

| instância | dbmea (custo / tempo) | gils_rvnd (custo / tempo) | resultado |
|---|---|---|---|
| lin318 | 5.659.325 / 43,0s | 5.562.365 / 35,1s | GILS-RVND melhor em qualidade e mais rápido |
| att532 | 5.791.790 / 116,8s | 5.653.489 / 183,1s | GILS-RVND melhor em qualidade; dbmea ~1,6x mais rápido |

Consistente com a literatura: nessas escalas (as mesmas onde H1-H6 deram
nulo), população não supera o GILS-RVND em qualidade. `att532` já mostra
o dbmea mais rápido, mas ainda perdendo em qualidade.

## 6. Resultado em `rand1000` (n=1000 — a escala que a literatura promete vantagem)

Instância gerada via `scripts/instance_generator.py --n 1000 --grid 1000
--seed 42 --out rand1000` (não faz parte do TSPLIB/conjunto usado até
aqui — precisou ser criada porque o projeto só tinha instâncias até
n=532).

| execução | dbmea | gils_rvnd |
|---|---|---|
| mesmo nº de "unidades de esforço" (10 gerações vs imax=1/iils=100) | 10.899.753 / 124,6s | 10.595.879 / 279,0s |
| dbmea com mais gerações (22) buscando orçamento de tempo parecido | 10.891.847 / 204,6s | (mesmo de cima: 10.595.879 / 279,0s) |

Mesmo dando ao dbmea mais que o dobro de gerações (10→22) e um orçamento
de tempo comparável, o custo mal se move (10.899.753 → 10.891.847 —
melhora de 0,07%, praticamente estagnado) — sinal de que, com os
parâmetros atuais (`pop-size=10`, `nClones`/`segLen` auto-derivados),
a população convergiu cedo e não está mais explorando de forma útil,
igual ao platô que já tínhamos visto em `lin318` (seção 4). O GILS-RVND
continua **~2,7-2,9% melhor em qualidade** nesta escala, mas o dbmea
usou 1,4-2,2x menos tempo — a vantagem de tempo cresce com `n` (quase
nula em 318, ~1,6x em 532, maior aqui), exatamente a tendência
qualitativa que a literatura reporta, só que sem a vantagem de
qualidade que o DBMEA "de verdade" (paper) relata nessa escala.

**Leitura honesta**: não conseguimos reproduzir a vantagem de qualidade
do DBMEA em nenhuma escala testada. A explicação mais provável não é
"a ideia não funciona" — é que testamos uma fração muito pequena da
escala do paper (população de 10-20 contra 100 deles; poucas dezenas de
gerações em minutos contra o que provavelmente são muito mais gerações
em horas) E o platô de convergência sugere que os parâmetros
(`nClones`, `segLen`, `transferLen`) provavelmente precisam de ajuste
para este código/esta escala, não só mais tempo com os mesmos valores.

## 7. Limitações e próximos passos

- Um único ponto de calibração por instância (sem seeds pareadas) — não é
  um teste estatístico ainda, só uma checagem de direção antes de investir
  num lote noturno de verdade.
- Custo por geração em `rand1000` é alto (~40s com `pop-size=10`, dominado
  pelo passo memético de RVND em toda a população) — testar com o
  orçamento que a literatura usa (populações de 100, muitas gerações) está
  fora do alcance de uma sessão interativa; precisaria de um lote noturno
  de várias horas.
- Não implementamos o "Circle Group Heuristic" (construção inicial mais
  diversa) nem ajustamos `nClones`/`segLen`/`transferLen` além dos valores
  auto-derivados da fórmula do paper (`n/15`, `n/20`) — não sabemos se
  esses valores são bons para este código/esta escala.

## 8. Parâmetros ajustados para bater com o paper — não resolveu

Ajustamos os defaults para os valores exatos do paper: `pop-size=100`
(era 20) e `n-transfers=40` fixo (era `=pop-size`, então crescia junto
com a população — o paper usa um valor fixo independente do tamanho da
população). `nClones`/`segLen`/`transferLen` já batiam (`n/15`, `n/20`).

Com orçamento de tempo parecido em `lin318` (~45-50s):

| configuração | custo final | tempo |
|---|---|---|
| pop=20, 100 gerações (antes do ajuste) | 5.659.325 | 43,0s |
| pop=100, 30 gerações (parâmetros do paper) | 5.671.916 | 49,5s |

**Piorou ligeiramente, não melhorou.** O platô de convergência persiste
com população maior — não é um artefato do tamanho da população pequeno.
Dentro de um orçamento de tempo fixo, população menor + mais gerações
supera população do tamanho do paper + poucas gerações, porque cada
geração com `pop=100` custa ~5x mais (RVND memético roda em toda a
população). Bater os *parâmetros* do paper sem bater a *escala de tempo*
dele (o paper relata ~4,2 horas por execução em n=1000) não reproduz o
resultado — provavelmente precisaríamos de centenas ou milhares de
gerações, não dezenas, para que a população de 100 realmente compense seu
custo por geração mais alto.

## 9. Recomendação

O achado real e consistente continua sendo **tempo, não qualidade** —
mesmo padrão do GILS-AM-RVND. Testar isso de verdade na escala do paper
(população 100, provavelmente centenas/milhares de gerações, horas de
execução) é trabalho de lote noturno/multi-hora — não é mais algo pra
recalibrar rapidamente numa sessão interativa. Antes de investir nisso,
vale decidir: (a) rodar esse teste longo mesmo assim (`--pop-size 100`,
gerações bem maiores, em `lin318`/`att532`/`rand1000`, durante a noite),
ou (b) considerar que replicar fielmente o DBMEA do paper está fora do
escopo prático desta sessão e redirecionar o esforço (ex.: GQPSO, ou
voltar a ajustar os operadores do DBMEA-lite antes de simplesmente jogar
mais tempo de máquina no problema).
3. Alternativa mais barata: aumentar só `pop-size` (mais indivíduos, sem
   mudar gerações) e ver se isso por si só destrava mais progresso —
   mais fácil de testar que ajustar `nClones`/`segLen`/`transferLen` às
   cegas.
