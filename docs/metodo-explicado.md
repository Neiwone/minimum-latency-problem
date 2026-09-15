# O método proposto, explicado do zero

> Documento didático, escrito para ser convertido em capítulo de texto acadêmico
> (`pandoc -f markdown -t latex`). Estrutura: `##` vira `\section`, `###` vira
> `\subsection`, blocos com crase tripla viram `verbatim`, `$...$` vira matemática
> inline. Os números experimentais vêm de
> [`experiments/h19-dlb-fast-regime.md`](experiments/h19-dlb-fast-regime.md) e
> [`experiments/h16-candidate-neighborhoods.md`](experiments/h16-candidate-neighborhoods.md).

---

## 1. O problema

### 1.1 Definição

No **Problema da Latência Mínima** (*Minimum Latency Problem*, MLP — também chamado
*Traveling Repairman Problem*), um veículo parte de um depósito e visita todos os
clientes exatamente uma vez. Diferente do Caixeiro Viajante, o objetivo **não** é
minimizar a distância total percorrida, e sim a **soma dos tempos de espera** dos
clientes.

Formalmente: seja uma rota $\pi = (\pi_0, \pi_1, \dots, \pi_{n-1})$, com $\pi_0 = 0$ o
depósito, e $d(u,v)$ o tempo de viagem entre $u$ e $v$. A **latência** do cliente na
posição $p$ é o instante em que ele é atendido:

$$\ell(p) = \sum_{q=1}^{p} d(\pi_{q-1}, \pi_q)$$

e o custo a minimizar é

$$f(\pi) = \sum_{p=1}^{n-1} \ell(p).$$

### 1.2 A intuição que governa tudo

Reescrevendo $f$ por aresta em vez de por cliente:

$$f(\pi) = \sum_{q=1}^{n-1} (n - q)\, d(\pi_{q-1}, \pi_q)$$

A aresta na posição $q$ é multiplicada por $(n-q)$ — ou seja, **é paga por todos os
clientes que ainda não foram atendidos**. Uma aresta ruim no início da rota é paga
por quase todo mundo; uma aresta ruim no fim é paga por quase ninguém.

Isso tem duas consequências que reaparecem no documento inteiro:

1. O objetivo é **posicional**: mover um cliente não afeta só os vizinhos dele, afeta
   o instante de chegada de todos os que vêm depois.
2. O objetivo **não é simétrico**: percorrer uma rota ao contrário, que no TSP custa
   o mesmo, no MLP custa outra coisa.

O MLP é NP-difícil, e métodos exatos não resolvem de forma consistente instâncias com
mais de aproximadamente 100 clientes. Daí o uso de metaheurísticas.

---

## 2. O algoritmo de referência: GILS-RVND

O ponto de partida deste trabalho é o **GILS-RVND** de Silva et al. (2012), que é o
estado da arte estabelecido para o MLP. Ele combina três ideias clássicas:

```
repita I_max vezes:                       <- multi-start
    s  <- construcao gulosa aleatorizada  <- GRASP
    s* <- s
    enquanto nao houver I_ILS fracassos seguidos:
        s <- busca_local(s)               <- RVND
        se f(s) < f(s*):  s* <- s
        s <- perturbacao(s*)              <- ILS
    guarda o melhor s* visto
```

Os três componentes:

- **GRASP** (*Greedy Randomized Adaptive Search Procedure*) — a construção. Monta uma
  rota escolhendo, a cada passo, um cliente sorteado entre os mais próximos (não
  necessariamente o mais próximo), o que gera pontos de partida diferentes a cada
  reinício.
- **RVND** (*Random Variable Neighborhood Descent*) — a busca local. Explicada na
  seção 3.
- **ILS** (*Iterated Local Search*) — o laço externo. Quando a busca local trava,
  aplica uma perturbação (chacoalhada) e busca de novo, a partir da melhor solução
  conhecida.

O parâmetro $I_{ILS}$ é **quantas perturbações seguidas sem melhora** o algoritmo
tolera antes de desistir daquela solução e reiniciar do zero.

**Praticamente todo o tempo de CPU está na busca local.** É nela que este trabalho
mexe.

---

## 3. Movimento, vizinhança e busca local

### 3.1 Movimento

Um **movimento** é uma alteração pequena e bem definida na ordem de visita. Uma
**vizinhança** é o conjunto de todas as soluções alcançáveis por um tipo de movimento.

Com a rota de exemplo

```
0 → 5 → 3 → 8 → 1 → 9 → 2 → 7 → 4 → 6
```

os movimentos usados neste trabalho são:

**Or-opt (realocação).** Retira um bloco de $L$ clientes consecutivos e o reinsere em
outra posição. Com $L = 2$:

```
antes:   0  5  3 [8  1] 9  2  7  4  6
depois:  0  5  3  9  2 [8  1] 7  4  6
```

**Or-opt invertido.** O mesmo, mas o bloco entra na ordem inversa:

```
depois:  0  5  3  9  2 [1  8] 7  4  6
```

No TSP esse movimento é quase redundante; no MLP **não é alcançável** por composição
dos demais, porque inverter um bloco realocado muda o instante de chegada de todos os
clientes dentro dele, não apenas das duas junções.

**Swap (troca).** Dois clientes trocam de posição.

**2-opt.** A definição clássica é *"dois arcos não adjacentes são removidos e outros
dois são inseridos de modo a formar uma nova rota viável"*. Concretamente, removendo
$(5,3)$ e $(9,2)$ e inserindo $(5,9)$ e $(3,2)$:

```
antes:   0 → 5 → 3 → 8 → 1 → 9 → 2 → 7 → 4 → 6
              ↑ remove          ↑ remove
depois:  0 → 5 → 9 → 1 → 8 → 3 → 2 → 7 → 4 → 6
              ↑ insere      ↑ insere
```

Para o resultado continuar sendo uma rota válida, o trecho entre os dois cortes tem
que ser percorrido **ao contrário**. Não é uma escolha de implementação: inverter o
trecho **é** a consequência de trocar aqueles dois arcos. Por isso o 2-opt aparece no
código como uma inversão de intervalo, e por isso, no MLP, ele altera o instante de
chegada de todos os clientes do trecho invertido.

Guardando os índices: se o trecho invertido vai da posição $i$ à posição $j$, os arcos
**removidos** são $(\pi_{i-1}, \pi_i)$ e $(\pi_j, \pi_{j+1})$, e os **inseridos** são
$(\pi_{i-1}, \pi_j)$ e $(\pi_i, \pi_{j+1})$. Essa observação é o que torna possível a
poda da seção 5.

### 3.2 Avaliação em tempo constante

Testar um movimento exige saber quanto ele muda o custo. Recalcular $f$ do zero custa
$O(n)$ por teste, o que inviabiliza qualquer busca local séria.

Silva et al. (2012) resolvem isso com **concatenação de subsequências**: a rota é vista
como emenda de trechos contíguos, e para cada trecho guarda-se o tempo de travessia, o
custo cumulativo interno e a quantidade de clientes. O custo de uma emenda sai desses
três valores em $O(1)$. Todo movimento acima é uma emenda de 3 a 5 trechos, logo é
avaliado em $O(1)$.

Este trabalho usa essa **regra** de avaliação sem alteração — ela é a contribuição
central do artigo de referência. O que muda é **como os três valores são obtidos**, que
é o assunto da subseção seguinte.

### 3.3 De três matrizes para dois vetores de prefixo

Para que a avaliação seja $O(1)$, os três valores de cada trecho precisam estar
disponíveis de imediato. A implementação de referência resolve isso **tabelando**: para
cada par de posições $(i,j)$ guarda o tempo de travessia $T(i,j)$, o custo cumulativo
$C(i,j)$ e o custo cumulativo do trecho percorrido ao contrário $C^{r}(i,j)$ — três
matrizes $n \times n$. E, como as tabelas descrevem a rota atual, elas precisam ser
**reconstruídas a cada movimento aplicado**, ao custo de $O(n^2)$.

A observação deste trabalho é que, para trechos **contíguos da rota atual**, as três
tabelas são redundantes: cada entrada é uma expressão $O(1)$ sobre dois vetores de
tamanho $n$. Defina

$$P[j] = \sum_{q=1}^{j} d(\pi_{q-1}, \pi_q), \qquad
  SP[j] = \sum_{q=0}^{j} P[q],$$

isto é, $P[j]$ é o instante de chegada na posição $j$ (a soma de prefixo das arestas) e
$SP$ é a soma de prefixo de $P$. Então:

$$T(i,j) = P[j] - P[i]$$

$$C(i,j) = \sum_{p=i+1}^{j}\bigl(P[p] - P[i]\bigr)
         = \bigl(SP[j] - SP[i]\bigr) - (j-i)\,P[i]$$

$$C^{r}(i,j) = \sum_{p=i}^{j-1}\bigl(P[j] - P[p]\bigr)
             = (j-i+1)\,P[j] - \bigl(SP[j] - SP[i] + P[i]\bigr)$$

A segunda linha é direta: no trecho percorrido no sentido normal, quem está na posição
$p$ espera $P[p] - P[i]$ desde a entrada do trecho. A terceira é a mesma soma no sentido
inverso — ali a entrada é $\pi_j$, e quem está em $p$ espera $P[j] - P[p]$. Em ambos os
casos o somatório de $P$ no intervalo sai de $SP$ em $O(1)$.

A quantidade de clientes do trecho é um simples $j - i + 1$ (com o depósito, que não é
cliente, descontado quando $i = 0$).

Três consequências:

1. Manter as estruturas passa de $O(n^2)$ para $O(n)$ por movimento aplicado — basta
   recalcular $P$ e $SP$.
2. O consumo de memória por solução cai de $3n^2$ inteiros para $2n$ — em `att532`, de
   $3{,}4$ MB de tabelas que não cabiam em cache para $8$ KB.
3. Como $P$ e $SP$ são **prefixos**, posições anteriores à primeira que o movimento
   mexeu não mudam de valor. Recalcular apenas a partir dali reduz ainda mais o custo,
   de $O(n)$ para $O(n - \ell o)$, onde $\ell o$ é a primeira posição afetada. É essa
   propriedade que a seção 7.2 explora.

A troca foi validada por **igualdade bit a bit** dos custos com a implementação
anterior, em `lin318`, `pr439` e `att532`: a trajetória de busca é idêntica, só o relógio
muda. O ganho medido é de $2{,}4$ a $2{,}9$ vezes em velocidade.

### 3.4 RVND

A **busca local** aplica movimentos que melhoram até nenhum melhorar mais; a solução
resultante é um **ótimo local**.

O RVND organiza as várias vizinhanças assim: mantém uma lista das vizinhanças ainda não
descartadas, sorteia uma, varre-a até o fim; se houve melhora, **repõe a lista inteira**
(vale a pena revisitar todas); se não houve, **remove** aquela vizinhança da lista. Para
quando a lista esvazia — ou seja, quando a solução é ótimo local de *todas* elas
simultaneamente. O sorteio evita o viés de uma ordem fixa de exploração.

---

## 4. O gargalo

Considere a vizinhança or-opt de bloco 1 numa instância com $n = 500$. Testar todas as
realocações possíveis são $500$ blocos $\times\ 500$ destinos $=$ **250 mil testes** —
e isso é *uma* varredura de *uma* vizinhança. Multiplicando pelas 13 vizinhanças e pelas
repetições que o RVND faz, uma única convergência custa centenas de milhões de
avaliações.

Sob orçamento de tempo fixo — 100 segundos por execução, que é o protocolo de
comparação usado aqui — **cada avaliação desperdiçada é qualidade perdida**. As três
seções seguintes atacam exatamente isso.

---

## 5. Primeira ideia: lista de candidatos

**Pergunta.** É mesmo necessário testar as 500 posições de destino para cada bloco?

**Observação.** Um movimento que melhora quase sempre cria uma aresta **curta**.
Realocar um cliente para um ponto do mapa distante de todo mundo não vai melhorar coisa
alguma.

**Mecanismo.** Para cada cidade $c$, pré-computa-se a lista das $K$ cidades
geograficamente mais próximas dela. Uma varredura só considera movimentos que criem uma
aresta entre a cidade e um desses $K$ vizinhos. Aplicado a cada vizinhança:

| vizinhança | regra de poda |
|---|---|
| or-opt (direto e invertido) | o bloco $[i..j]$ tem que cair ao lado de um vizinho próximo de $\pi_i$ ou de $\pi_j$ |
| 2-opt | o arco inserido é $(\pi_{i-1}, \pi_j)$, logo $\pi_j$ tem que ser vizinho próximo de $\pi_{i-1}$ |
| swap | $\pi_j$ passa a ficar entre $\pi_{i-1}$ e $\pi_{i+1}$, mesma regra |

Cada varredura passa de $O(n^2)$ para $O(nK)$. Com $K = 12$ e $n = 500$, são
$40\times$ menos testes.

**O preço.** É uma restrição heurística: movimentos de melhora cujas arestas novas
sejam todas longas deixam de ser enxergados. Troca-se profundidade do ótimo local por
quantidade de iterações — e é exatamente essa a troca que um orçamento de tempo fixo
premia.

**Calibração.** $K = 12$; $K = 20$ e $K = 30$ foram testados e ficaram $0{,}25\%$ a
$0{,}32\%$ **piores**: mais candidatos custam mais tempo sem entregar qualidade.

---

## 6. Segunda ideia: *don't-look bits*

**Pergunta.** Depois que a busca local convergiu e a rota foi perturbada, é mesmo
necessário reexaminar as 500 cidades?

**Observação.** A perturbação mexeu num pedaço da rota. Uma cidade que está num trecho
não mexido continua exatamente na mesma situação de antes — e antes já havia sido
concluído que ela não tinha movimento de melhora. Testá-la de novo é refazer uma conta
cujo resultado já se conhece.

**Mecanismo.** Um sinalizador por cidade, o *don't-look bit* (Bentley, 1992), que
responde "vale a pena olhar para esta cidade?".

- Começa ligado em todas.
- As varreduras **pulam** cidades com o sinalizador desligado.
- Uma cidade examinada sem render movimento tem o sinalizador **desligado**.
- Quando algo perto dela muda, o sinalizador é **religado**.

Como há 13 vizinhanças, o sinalizador não é um booleano: é um conjunto de 13 bits, um
por vizinhança, e a cidade só sai de circulação quando **todas** a examinaram sem
sucesso. Qualquer religamento zera o conjunto inteiro.

O estado persiste **entre** chamadas da busca local — é o que permite, depois de uma
perturbação, religar apenas a região afetada em vez da rota toda.

---

## 7. Terceira ideia: o *span*, e por que ele basta

O *don't-look bit* precisa saber **quais cidades religar**. A resposta é o **span**: o
intervalo de posições da rota que a mudança mexeu.

### 7.1 O span de uma perturbação

A perturbação usada é o *double bridge*: corta a rota em quatro pedaços e troca os dois
do meio de lugar.

```
antes:   [ A A A ] [ B B ] [ C C C ] [ D D D D ]
depois:  [ A A A ] [ C C C ] [ B B ] [ D D D D ]
           intacto  └──── mexido ────┘  intacto
```

Os pedaços $A$ e $D$ mantêm as mesmas cidades nas mesmas posições. O span é o miolo —
na prática, um par (primeira posição mexida, última posição mexida). Religam-se apenas
as cidades ali dentro, **mais as duas das bordas**: elas não se moveram, mas ganharam
um vizinho novo.

### 7.2 O span de um movimento aplicado

O mesmo vale dentro da busca local. Uma realocação de bloco desloca um intervalo de
posições; uma inversão de 2-opt mexe no intervalo invertido. Em ambos os casos o span é
conhecido de graça, e só ele é religado.

Isso permite ainda uma segunda economia: as estruturas auxiliares da avaliação são
prefixos acumulados ao longo da rota, então posições **antes** do span não mudam.
Recalcular apenas a partir da primeira posição mexida troca um custo $O(n)$ por
movimento por um custo proporcional ao que de fato mudou.

### 7.3 Por que é lícito ignorar o resto

Esta é a única parte do método que exige um argumento específico do MLP, e ela é
necessária: como o objetivo é posicional, seria natural supor que reordenar um trecho
altera o valor de **todos** os movimentos posteriores. Não altera.

Seja $W = [a,b]$ a janela de posições reordenada. Fora de $W$ nenhuma cidade muda de
posição, e dentro de $W$ o conjunto de cidades é o mesmo — só a ordem muda. Escrevendo
o custo total separando prefixo, janela e sufixo, e chamando de $T_{pre} = \ell(a-1)$ a
duração acumulada até a entrada da janela:

$$f(\pi) = \underbrace{\sum_{p<a} \ell(p)}_{\text{prefixo}}
        + \underbrace{(b-a+1)\,T_{pre} + C_W}_{\text{janela}}
        + \underbrace{(n-1-b)\,(T_{pre} + T_W) + C_S}_{\text{sufixo}}$$

onde $C_W$ é o custo cumulativo interno da janela, $T_W$ o tempo de travessia dela e
$C_S$ o custo cumulativo interno do sufixo.

O termo $T_{pre}$ aparece multiplicado por $(b-a+1) + (n-1-b) = n-a$, que é uma
**contagem de clientes** — e reordenar a janela não muda quantos clientes existem antes
ou depois dela. Logo o coeficiente é o mesmo nas duas configurações, e $T_{pre}$
**cancela** na diferença.

Aplicando o mesmo raciocínio a um movimento candidato $\mu$ que opera inteiramente
**antes** ou inteiramente **depois** de $W$: o ganho de $\mu$ depende apenas das
cidades que $\mu$ reordena, da cidade que entra na janela de $\mu$, e de contagens de
clientes — nenhum desses elementos é tocado pela reordenação de $W$. Portanto o ganho
de $\mu$ **não muda**, e reexaminá-lo seria refazer uma conta já feita.

Ficam de fora duas classes, e ambas estão tratadas:

- Movimentos cuja janela **começa exatamente na junção** de $W$: a cidade de entrada
  deles mudou. São cobertos pelo religamento das duas bordas (o $\pm 1$).
- Movimentos que **atravessam** $W$ — pegam um bloco de um lado e o inserem do outro.
  Esses de fato mudam de valor e ficam invisíveis. É o mesmo tipo de aposta da lista de
  candidatos: perde-se um subconjunto de movimentos em troca de velocidade.

### 7.4 Efeito medido

A busca local passa a fazer de **2 a 10 vezes mais iterações de ILS por segundo**. Em
`lin318` com $I_{ILS} = 100$ e 30 segundos de orçamento: 2 reinícios completos sem os
sinalizadores, 19 com eles.

---

## 8. Quarta ideia: recalibrar $I_{ILS}$

$I_{ILS}$ responde "quantas perturbações seguidas sem melhora antes de descartar esta
solução e reiniciar do zero?".

O protocolo de comparação em uso no projeto fixava $I_{ILS} = 10$ para todos os
algoritmos. Esse valor não havia sido escolhido por qualidade: ele existia para garantir
que os mecanismos de um dos algoritmos comparados, que só agem na fronteira de reinício,
fossem exercitados dentro do orçamento.

O problema é estrutural: **um reinício joga fora a solução incumbente** para recomeçar
de uma construção gulosa, e a descida a partir de uma construção é a mais cara de toda a
execução — além de terminar num ótimo local tipicamente pior do que aquele que acabou
de ser descartado. Quanto mais rápida a busca local, maior o peso relativo desse
desperdício.

Elevando para $I_{ILS} = 300$, o orçamento passa a ser gasto **aprofundando uma
trajetória** em vez de visitar muitos ótimos locais rasos. Em `att532`, a configuração
proposta completa 8 reinícios em 100 segundos, contra 224 da configuração anterior.

O ganho isolado desta mudança é de $0{,}65\%$, com vitória em 18 de 18 comparações
pareadas. $I_{ILS} = 1000$ e $3000$ já pioram, então 300 é um ótimo real, não uma
monotonia.

---

## 9. Resumo das diferenças

| # | Componente | GILS-RVND | Método proposto |
|---|---|---|---|
| 1 | Estruturas de avaliação (§3.3) | 3 matrizes $n \times n$ refeitas a cada movimento | 2 vetores de prefixo, atualização $O(n)$ |
| 2 | Vizinhanças | 5 | 13 (or-opt 1–6 + or-opt invertido 2–6) |
| 3 | Varredura | $O(n^2)$ completa | podada por lista de $K=12$ candidatos, $O(nK)$ |
| 4 | Ordem de varredura | recomeça a cada movimento aplicado | contínua, guiada por *don't-look bits* |
| 5 | Aplicação de movimento | $O(n)$ | proporcional ao span |
| 6 | Construção | GRASP puro | GRASP com memória adaptativa de arestas |
| 7 | $I_{ILS}$ | 100 | 300 |
| 8 | Critério de parada | número de iterações | tempo de parede |

O esqueleto — GRASP + ILS + RVND, perturbação por *double bridge*, aceitação estrita,
avaliação $O(1)$ por concatenação de subsequências — **permanece o mesmo**.

---

## 10. Resultados

Protocolo: 100 segundos de tempo de parede por execução, idênticos para todos os
algoritmos; execuções sequenciais (comparação de tempo não sobrevive a disputa por CPU);
10 sementes pareadas por instância; 7 instâncias com $n \geq 200$; teste dos sinais
bilateral exato.

Comparação contra o **MDM-GILS-RVND** (Silva et al., 2019 — GILS-RVND com mineração de
padrões), 70 pares:

| linha de base | diferença média | V/E/D | $p$ |
|---|---:|---:|---:|
| MDM-GILS-RVND (configuração do protocolo) | $-1{,}249\%$ | 60/10/0 | $< 10^{-6}$ |
| MDM-GILS-RVND na melhor calibração dele | $-0{,}358\%$ | 46/19/5 | $< 10^{-6}$ |

Valores negativos significam custo menor, isto é, melhor. Contra a configuração do
protocolo o método proposto **não perde uma única semente em 70**; os 10 empates são
todos de uma instância que satura dentro do orçamento.

Em termos de distância para a melhor solução conhecida, nas três maiores instâncias
TSPLIB o *gap* médio cai de $1{,}26\%$ (MDM-GILS-RVND) para aproximadamente $0\%$. O
método encontra o ótimo conhecido de `lin318` e de `pr439` dentro dos 100 segundos, e em
`att532` produziu uma solução $0{,}28\%$ melhor do que a melhor até então registrada no
projeto.

---

## 11. O que foi testado e rejeitado

Todas as alternativas abaixo foram implementadas, verificadas (rota válida e custo
recalculado a partir das coordenadas) e testadas com sementes pareadas. Nenhuma entrou:

| mudança | resultado |
|---|---|
| $K = 20$ / $K = 30$ na lista de candidatos | $+0{,}32\%$ / $+0{,}25\%$ |
| blocos de or-opt até 3, 4, 8 ou 10 | $+0{,}05\%$ a $+0{,}11\%$ |
| âncoras de or-opt no início da rota | $+0{,}34\%$ |
| 2-opt ancorado nos dois arcos inseridos | $+0{,}12\%$ |
| aceitação por limiar no ILS | $+0{,}17\%$ |
| polimento com busca local completa a cada novo melhor global | $+0{,}13\%$ |
| *crossover* baseado em arcos entre soluções elite | $+0{,}26\%$ |
| reinício por perturbação forte da incumbente | $+0{,}26\%$ ($p = 0{,}008$) |
| *double bridge* com blocos de tamanho limitado | nulo |
| perturbação enviesada para o início da rota | $+0{,}12\%$ a $+0{,}33\%$ |
| *don't-look bits* estritos (pular par cidade–vizinhança já falhado) | nulo ($1{,}6\times$ mais rápido, mesma qualidade) |

O padrão é consistente e vale como conclusão própria: **no MLP, mecanismos que alteram
de onde a busca recomeça não sobrevivem à busca local — o que paga é vizinhança e
velocidade.**

---

## Referências

- SILVA, M. M.; SUBRAMANIAN, A.; VIDAL, T.; OCHI, L. S. A simple and effective
  metaheuristic for the Minimum Latency Problem. *European Journal of Operational
  Research*, v. 221, n. 3, p. 513–520, 2012.
- BENTLEY, J. L. Fast algorithms for geometric traveling salesman problems. *ORSA
  Journal on Computing*, v. 4, n. 4, p. 387–411, 1992.
- SALEHIPOUR, A.; SÖRENSEN, K.; GOOS, P.; BRÄYSY, O. Efficient GRASP+VND and GRASP+VNS
  metaheuristics for the traveling repairman problem. *4OR*, v. 9, n. 2, p. 189–209,
  2011.
- REN, J.; HAO, J.-K.; WU, F.; FU, Z.-H. An effective hybrid search algorithm for the
  multiple traveling repairman problem with profits. *European Journal of Operational
  Research*, v. 304, n. 2, p. 381–394, 2023.
- TOTH, P.; VIGO, D. The granular tabu search and its application to the vehicle
  routing problem. *INFORMS Journal on Computing*, v. 15, n. 4, p. 333–346, 2003.
