# Busca local podada e *don't-look bits*: o que mudou e o que os números mostram

Documento autocontido: não pressupõe acompanhamento do dia a dia do projeto. Resume o
que mudou, por quê, como foi medido e o que os números permitem afirmar.

---

## 1. Resumo

O gargalo de qualidade do GILS-RVND sob orçamento de tempo fixo é a **busca local**,
não a estratégia de busca. Trocando a busca local por uma versão podada e guiada por
*don't-look bits*, e recalibrando um parâmetro do ILS, a qualidade a 100 segundos por
execução melhora:

| comparação | ganho | resultado |
|---|---:|---|
| vs MDM-GILS-RVND, TSPLIB n ≥ 200 (5 instâncias) | **−0,86%** | 40 vitórias / 10 empates / 0 derrotas em 50 pares |
| vs MDM-GILS-RVND, Salehipour n = 500 (20 instâncias) | **−1,99%** | 80 / 0 / 0 em 80 pares |
| vs MDM-GILS-RVND, Salehipour n = 1000 (20 instâncias) | **−3,37%** | 60 / 0 / 0 em 60 pares |

Nenhuma seed perdida em 190 pares (os 10 empates são todos de uma instância que
satura), e o efeito cresce com o tamanho da instância.

O segundo resultado é um **controle**, e é o mais interessante: dando a mesma busca
local ao MDM-GILS-RVND e ao GILS-RVND puro, os três **empatam**. Ou seja, o ganho vem
da busca local, e os dois mecanismos de memória publicados para o problema
(mineração de padrões e memória adaptativa) são indistinguíveis de **não ter mecanismo
nenhum**.

Ao longo do trabalho, 1.941 execuções medidas e verificadas, e duas melhores soluções
conhecidas do projeto atualizadas.

---

## 2. O problema

No **Problema da Latência Mínima** (MLP), um veículo sai de um depósito e visita todos
os clientes uma vez. Diferente do Caixeiro Viajante, o objetivo não é minimizar a
distância percorrida, e sim a **soma dos tempos de espera** dos clientes.

Reescrevendo o custo por aresta em vez de por cliente:

```
custo = soma sobre as arestas de  (quantos clientes ainda faltam) x (comprimento da aresta)
```

Uma aresta no início da rota é paga por quase todos os clientes; uma no fim, por quase
ninguém. Daí duas consequências que aparecem o tempo todo:

- o objetivo é **posicional** (mexer num cliente muda o instante de chegada de todos os
  seguintes);
- o objetivo **não é simétrico** (percorrer um trecho ao contrário custa outra coisa).

O MLP é NP-difícil e métodos exatos não passam de forma consistente de ~100 clientes,
o que justifica metaheurísticas.

---

## 3. O ponto de partida

O projeto é construído sobre o **GILS-RVND** (Silva, Subramanian, Vidal & Ochi, *EJOR*
221, 2012), que é a referência estabelecida para o MLP. Ele repete:

1. **construir** uma rota gulosa aleatorizada;
2. **melhorar** com busca local até travar;
3. **perturbar** e voltar ao passo 2;
4. depois de `I_ILS` perturbações seguidas sem melhora, descartar tudo e **reiniciar**.

A comparação de referência é o **MDM-GILS-RVND** (Santana, Plastino & Rosseti, 2019),
que acrescenta mineração de padrões: guarda as melhores soluções, minera trechos de
rota frequentes entre elas e os injeta em construções novas.

Antes deste trabalho, o melhor resultado do projeto contra o MDM a 100 s era −0,65%
em três instâncias TSPLIB.

---

## 4. O diagnóstico: onde o tempo é gasto

Praticamente todo o tempo de CPU está na busca local. E ela é cara de um jeito
específico: para cada tipo de movimento, ela testa todas as posições contra todas as
posições.

Numa instância com 500 clientes, testar todas as realocações de um cliente são
`500 x 500 = 250 mil` avaliações — e isso é **uma** varredura de **um** tipo de
movimento, entre treze, repetida várias vezes até nada mais melhorar.

Com o tempo fixo em 100 segundos, **cada avaliação desperdiçada é qualidade perdida**.
Foi esse o alvo.

---

## 5. O que foi mudado

Quatro mudanças, nenhuma delas de estratégia de busca.

### 5.1 Lista de candidatos

*Pergunta:* é preciso mesmo testar as 500 posições de destino para cada cliente?

*Observação:* um movimento que melhora quase sempre cria uma aresta **curta**.
Realocar um cliente para longe de todo mundo não vai melhorar nada.

*Mecanismo:* para cada cidade, pré-computar as **12 cidades mais próximas**; só testar
movimentos que criem uma aresta para uma delas. A varredura passa de `500 x 500` para
`500 x 12`.

*Preço:* movimentos de melhora cujas arestas novas sejam todas longas deixam de ser
vistos. Troca profundidade por quantidade de iterações — a troca que um orçamento de
tempo premia. Testado: 12 vizinhos é melhor que 20 e que 30.

### 5.2 *Don't-look bits*

*Pergunta:* depois de perturbar a rota, é preciso reexaminar todos os 500 clientes?

*Observação:* a perturbação mexe num pedaço da rota. Um cliente num trecho intocado
está na mesma situação de antes — e antes já se concluiu que ele não tinha movimento de
melhora. Testar de novo é refazer uma conta cujo resultado já se sabe.

*Mecanismo:* um sinalizador por cidade ("vale a pena olhar aqui?"), desligado quando a
cidade é examinada sem render movimento e religado quando algo perto dela muda.
Técnica clássica em TSP (Bentley, 1992).

*A parte específica do MLP:* como o objetivo é posicional, seria natural supor que
reordenar um trecho muda o valor de **todos** os movimentos posteriores. Não muda. O
atraso acumulado entra no custo de um trecho posterior sempre multiplicado pelo
**número de clientes** que vêm depois — e reordenar um trecho não muda quantos clientes
existem, só a ordem. Esse termo é o mesmo antes e depois, e cancela quando se calcula
o ganho do movimento. A regra usada é, portanto, "religue toda cidade cuja **posição**
mudou, mais as duas das bordas". É exata para movimentos de um lado só do trecho
perturbado, e aproximada apenas para os que o atravessam.

*Efeito:* de 2 a 10 vezes mais iterações por segundo. Em `lin318`, com o mesmo
parâmetro: 2 reinícios completos em 30 segundos sem os sinalizadores, 19 com eles.

### 5.3 Aplicação de movimento proporcional ao que mudou

Aplicar um movimento custava tempo proporcional ao tamanho da rota inteira. Mas
realocar um bloco é uma **rotação** de um intervalo, e as estruturas auxiliares da
avaliação são somas de prefixo — nada antes da primeira posição mexida muda. Passou a
recalcular só dali em diante.

### 5.4 Recalibrar `I_ILS`

`I_ILS` é "quantas perturbações seguidas sem melhora antes de descartar a solução e
reiniciar do zero". O protocolo de testes do projeto usava **10**, um valor escolhido
por razões de protocolo, não de qualidade.

O problema é estrutural: **um reinício joga fora a solução boa** para recomeçar de uma
construção gulosa, cuja descida é a mais cara de toda a execução e termina num ponto
pior. Quanto mais rápida a busca local, mais caro fica esse desperdício.

Subindo para **300**, o orçamento passa a aprofundar **uma** trajetória em vez de
visitar muitos ótimos locais rasos. Sozinha, essa mudança vale **0,65%**, com vitória
em 18 de 18 comparações. Testado também 1000 e 3000, ambos piores — 300 é um ótimo
real.

---

## 6. Como foi medido

Comparar estes algoritmos pelo número de iterações compara orçamentos de computação
diferentes, porque o custo por iteração varia muito entre eles. Por isso o protocolo é
de **tempo fixo**: 100 segundos de relógio para todos, idênticos.

Regras seguidas em todos os lotes:

- **execuções sequenciais**, uma por vez: comparação de tempo não sobrevive a disputa
  por CPU (medido: 3 processos concorrentes custam 27% da vazão);
- **pareamento por seed**: a mesma semente aleatória para todos os algoritmos em cada
  instância, e a comparação é par a par;
- **teste dos sinais bilateral exato** sobre os pares;
- **verificação independente** dos tours: toda rota reportada é conferida como
  permutação válida e tem a latência recalculada a partir das coordenadas do arquivo,
  com a mesma convenção de arredondamento — o custo reportado pelo solver nunca é
  aceito de palavra.

Instâncias: TSPLIB na variante caminho hamiltoniano (`pr226`, `a280`, `lin318`,
`pr439`, `att532`) e o benchmark de Salehipour et al. (2011), 20 instâncias por
tamanho, nos tamanhos 500 e 1000.

---

## 7. Resultados

### 7.1 Contra o MDM-GILS-RVND publicado

| conjunto | instâncias | seeds | pares | mean_rel% | V/E/D | p |
|---|---:|---:|---:|---:|---:|---:|
| TSPLIB n ≥ 200 | 5 | 10 | 50 | **−0,855** | 40/10/0 | < 10⁻⁹ |
| Salehipour n = 500 | 20 | 4 | 80 | **−1,987** | 80/0/0 | < 10⁻²³ |
| Salehipour n = 1000 | 20 | 3 | 60 | **−3,372** | 60/0/0 | < 10⁻¹⁷ |

`mean_rel%` é a média, sobre os pares, de `(custo_proposta − custo_MDM)/custo_MDM`;
negativo é melhor.

Nos dois tiers Salehipour a proposta venceu em **todas as seeds das 20 instâncias**.
Tomando cada instância como uma observação, isso é 20/20, p ≈ 2·10⁻⁶ por tier.
Instância mais fraca em n=1000: −2,94%. Mais forte: −3,81%.

O efeito cresce monotonicamente com o tamanho:

| instância / tier | n | ganho |
|---|---:|---:|
| `pr226` | 226 | 0,00% (satura: todos acham o mesmo custo) |
| `a280` | 280 | −0,52% |
| `lin318` | 318 | −0,42% |
| `pr439` | 439 | −1,20% |
| `att532` | 532 | −2,13% |
| Salehipour | 500 | −1,99% |
| Salehipour | 1000 | **−3,37%** |

Os dez empates do conjunto TSPLIB são todos de `pr226`, onde os três algoritmos acham
a mesma solução em todas as seeds.

**As tabelas completas — por instância, com custos absolutos, os controles e a
sanidade do protocolo — estão em [`results-tables.md`](../results-tables.md)**,
geradas diretamente dos dados brutos por `scripts/make_result_tables.py`.

### 7.2 O controle: de onde vem o ganho

A comparação acima é entre **implementações**: o MDM-GILS-RVND varre todo o espaço de
posições, sem lista de candidatos nem *don't-look bits*. Para separar "busca local
melhor" de "estratégia melhor", a busca local foi portada para os outros dois
algoritmos e os cinco braços foram medidos nos mesmos lotes. O que resta entre eles é
só o mecanismo de memória.

Comparados contra o braço **sem mecanismo de memória nenhum**:

| braço | n = 500 (80 pares) | n = 1000 (60 pares) | TSPLIB* (30 pares) |
|---|---|---|---|
| memória adaptativa (a proposta) | −0,023% (p = 0,58) | +0,005% (p = 0,52) | −0,017% (p = 0,54) |
| mineração de padrões (MDM) | −0,026% (p = 0,39) | +0,012% (p = 0,61) | +0,003% (p = 0,63) |

\* a coluna TSPLIB é de um lote anterior, restrito a `lin318`/`pr439`/`att532`.

**Empate em tudo.** Nenhuma instância isolada significativa em nenhum par.

Um quinto braço foi incluído de propósito: o MDM com `I_ILS` menor, em que a mineração
dele roda com bastante folga (2,4 minerações por execução em n=1000, contra 0,8). Era
para responder à objeção "o mecanismo deles mal rodou". O resultado foi além do
esperado:

| | n = 500 | n = 1000 |
|---|---|---|
| MDM com a mineração rodando com folga, vs sem memória | +0,089% (p = 0,013) | **+0,490% (p < 10⁻⁶)** |

Fazer o mecanismo atuar mais não é neutro: é **pior**. Ele consome reinícios e
iterações, e esse custo aparece no resultado.

*(Nota de protocolo: o braço do MDM com `I_ILS = 300` teve 14 de 60 execuções sem
nenhuma mineração em n=1000 — exatamente a fragilidade que o quinto braço cobre.)*

### 7.3 Soluções novas

Duas melhores soluções conhecidas do projeto foram atualizadas, ambas verificadas
recalculando a latência a partir das coordenadas:

| instância | antes | agora |
|---|---:|---:|
| `att532` | 5 589 568 | **5 573 783** (−0,28%) |
| `a280` | sem registro | **340 998** (as 5 seeds acham o mesmo valor) |

Em `lin318` e `pr439` a proposta encontra o melhor valor conhecido dentro dos 100
segundos, de modo que não havia o que melhorar.

---

## 8. O que os números permitem afirmar

Três afirmações, nesta ordem de força:

1. **A configuração proposta bate o MDM-GILS-RVND publicado**, e a vantagem cresce com
   o tamanho da instância, chegando a −3,37% em n = 1000 sem perder uma seed.
2. **O ganho é da busca local e da calibração, não da estratégia de busca.** Dada ao
   MDM, a mesma busca local o leva ao mesmo patamar.
3. **Sob uma busca local suficientemente rápida, os dois mecanismos de memória
   publicados para o MLP são indistinguíveis de não ter mecanismo nenhum** — e
   forçá-los a atuar mais piora o resultado.

A terceira é a mais interessante e a que menos se esperava. Ela é consistente com o
que as hipóteses anteriores do projeto vinham encontrando por dentro (perturbação
adaptativa, *path relinking*, algoritmo memético populacional, *ruin-and-recreate*,
*guided local search* — todas nulas), mas agora está verificada contra dois mecanismos
**publicados**, e não contra ideias próprias.

---

## 9. O que foi testado e não funcionou

Todas as alternativas abaixo foram implementadas, verificadas e testadas com seeds
pareadas antes de serem descartadas. O sinal é sempre a diferença contra a
configuração adotada; positivo é pior.

| mudança testada | resultado |
|---|---|
| lista de candidatos com 20 / 30 vizinhos | +0,32% / +0,25% |
| blocos de realocação de comprimento 3, 4, 8 ou 10 (em vez de 6) | +0,05% a +0,11% |
| âncoras de realocação no início da rota | +0,34% |
| 2-opt ancorado também na segunda aresta criada | +0,12% |
| aceitação por limiar no ILS | +0,17% |
| polimento com busca local completa a cada novo melhor global | +0,13% |
| *crossover* entre soluções elite (Ren, Hao, Wu & Fu, *EJOR* 304, 2023) | +0,26% |
| reinício por perturbação forte em vez de construção nova | +0,26% (p = 0,008) |
| perturbação com blocos de tamanho limitado | nulo |
| perturbação enviesada para o início da rota | +0,12% a +0,33% |
| *don't-look bits* estritos | nulo (1,6× mais rápido, mesma qualidade) |

O padrão é consistente com a conclusão da seção 8: **mecanismos que mudam de onde a
busca recomeça não sobrevivem à busca local; o que paga é vizinhança e velocidade.**

---

## 10. Limitações

1. **`I_ILS = 300` foi calibrado nesta faixa de tamanho e neste orçamento.** Em
   instâncias pequenas a busca satura muito antes, e com outro orçamento o valor
   provavelmente muda.
2. **As duas podas são heurísticas.** A lista de candidatos perde movimentos cujas
   arestas novas sejam todas longas; os *don't-look bits* perdem movimentos que
   atravessam o trecho perturbado. Não há garantia de terminar no mesmo ótimo local que
   a varredura completa — o que os números dizem é que a troca compensa.
3. **Uma máquina por lote.** Cada lote é internamente comparável (todos os braços na
   mesma máquina, sequencialmente), mas lotes de máquinas diferentes não devem ser
   comparados entre si, e não foram.
4. **Poucas seeds por instância nos tiers grandes** (3 em n=1000, 4 em n=500). Isso é
   suficiente para o teste agregado, mas nenhuma instância isolada pode atingir
   significância sozinha com tão poucas repetições — a força vem do conjunto.
5. **Uma ineficiência conhecida e não corrigida:** a lista de vizinhos do projeto
   guarda a própria cidade na primeira posição, então `12 vizinhos` na prática são 11
   mais uma avaliação inútil por varredura (~8% do custo do scan). Corrigir mudaria o
   parâmetro efetivo de todas as calibrações já feitas, então ficou pendente.

---

## 11. Próximos passos possíveis

- **Comparar com os valores publicados na literatura** para as instâncias Salehipour,
  em vez de apenas com as reimplementações deste projeto.
- **Corrigir a ineficiência da seção 10.5** e recalibrar o número de vizinhos.
- **Testar o tier n = 200** para fechar a curva de crescimento do efeito com `n`.
- **Investigar por que o mecanismo de memória não paga**, que é a pergunta aberta mais
  interessante: se o custo em iterações explica tudo, ou se os padrões minerados
  simplesmente não carregam informação útil sob este objetivo.

---

## 12. Onde está cada coisa

| o quê | onde |
|---|---|
| configuração proposta | `./bin/gils_am_rvnd --rvnd-mode candidate-dlb --cand-k 12 --iils 300 --max-time 100` |
| busca local nova | `src/neighborhoods_cand.cpp`, `include/neighborhoods_cand.h` |
| o mesmo, portado para os outros dois | `src/mdm_gils_rvnd.cpp`, `src/gils_rvnd.cpp` |
| runner de experimentos | `run_experiments.py --mode fixed-time` |
| verificador independente de tours | `scripts/verify_tour.py` |
| dados brutos dos lotes finais | `results/fixed-time/advisor_n500_100s.json`, `results/fixed-time/advisor_n1000_100s.json` |
| dados dos lotes TSPLIB | `scripts/fixed_time_100s*.json` |
| registro completo do experimento | `docs/hypotheses/h19-dlb-fast-regime.md` |
| o método explicado em detalhe | `docs/concepts/method-explained.md` |
| diferenças linha a linha vs GILS-RVND | `docs/concepts/proposal-vs-gils-rvnd.md` |
| hipóteses anteriores (todas documentadas) | `docs/hypotheses/` |
