# H20 — A memória adaptativa contribui em algo além da qualidade?

**Veredito: sim, em velocidade; não em qualidade final.** Isolando só a memória (mesmo
binário e mesma construção, λ = 0 contra λ = 0,5):

| critério | resultado |
|---|---|
| **tempo, a iterações fixas** | **−19% a −24%** para a mesma qualidade (18/0/2, p = 0,0004; 16/0/4, p = 0,012) |
| qualidade, a iterações fixas | empate (+0,003% e +0,025%) |
| qualidade, 100 s, `I_ILS` = 300 (o método proposto) | empate (+0,004%, 14/9/7, p = 0,19) |
| qualidade, 100 s, `I_ILS` = 30 (muitos reinícios) | −0,121% (20/0/10, p = 0,099), não significativo |
| custo ao longo do tempo, `I_ILS` = 30 | **−0,29% aos 10 s** (20/6/4, p = 0,0015); a vantagem some depois |
| diversidade dos reinícios | **menor**: distância até a melhor solução cai de 36% para 22% dos nós |
| robustez (desvio, pior caso) | sem padrão: melhora em umas instâncias, piora em outras |

A memória é um mecanismo de **eficiência**, não de exploração. Ela faz cada reinício
começar perto da melhor solução já vista, então o reinício é mais curto e chega ao
mesmo nível de qualidade com menos trabalho. O preço é diversidade: os reinícios ficam
parecidos com a solução que já se tem, e uma parte deles volta exatamente ao mesmo ótimo.
Com tempo fixo, o tempo economizado vira mais reinícios, mas reinícios menos diversos,
e o saldo em qualidade é nulo. No método proposto há ainda um limite prático: em 19 de
30 execuções há um único reinício, e a memória nunca chega a agir.

---

## Hipótese

A [ablação](../reports/ablation-gils-rvnd-to-dlb.md) e o controle de justiça do
[H19](h19-dlb-fast-regime.md) mostraram que a memória adaptativa não melhora a
qualidade final a tempo fixo. Mas o
[grasp-am-large-scale](grasp-am-large-scale.md) tinha registrado um efeito colateral:
com iterações fixas, o `gils_am_rvnd` chegava ao mesmo resultado 20–26% mais rápido que
o `gils_rvnd`. Aquela comparação tinha um confundidor: o `gils_am_rvnd` também troca a
construção (RCL por limiar, sem `sort`). A pergunta aqui é se a memória, **isolada**,
contribui por outros critérios:
1. velocidade;
2. desempenho ao longo do tempo (*anytime*);
3. tempo até atingir um alvo;
4. robustez;
5. o que ela muda em cada reinício.

## O que foi testado

**Isolamento.** Todo par compara `gils_am_rvnd --lambda 0` (sem memória: o bônus de
frequência é zero, a construção vira GRASP puro com RCL por limiar) contra
`--lambda 0.5` (o padrão), no mesmo binário e com a mesma busca local. A única
diferença é a memória.

**Instrumentação.** A flag `--trace` do `gils_am_rvnd` imprime uma linha por reinício
(custo construído, custo e duração da primeira descida, ótimo do reinício, iterações de
ILS, duração, distância até a melhor solução global) e uma por nova melhor solução
global (instante e custo). A flag só imprime; a busca é bit a bit idêntica com e sem
ela. A distância entre duas rotas é o número de nós cujo sucessor difere, em % de n.

**Dois protocolos**, ambos sequenciais, porque tempo é uma das medidas:

| protocolo | o que mede | braços | instâncias | execuções |
|---|---|---|---|---:|
| **iterações fixas** (`I_max` = 10, `I_ILS` = 100, sem limite de tempo) | tempo para o mesmo trabalho, como no grasp-am-large-scale | λ ∈ {0; 0,5} × busca local ∈ {original; `candidate-dlb`} | `kroA200`, `a280`, `lin318`, `pr439` | 80 |
| **tempo fixo** (100 s) | qualidade, custo ao longo do tempo, tempo até o alvo, mecanismo | λ ∈ {0; 0,5} × `I_ILS` ∈ {30; 300} | as 6 da ablação (`att532` a `nrw1379`, n ≥ 500) | 120 |

Seeds 1–5, pareadas. Todos os tours foram verificados a partir das coordenadas.
`I_ILS` = 300 é o método proposto; `I_ILS` = 30 dá muitos reinícios, para a memória
ter onde agir.

A `att532` foi retirada do protocolo de iterações fixas durante a execução: com a busca
local original, cada execução levava ~33 min, e as 17 restantes custariam ~5 h. As 3
execuções feitas ficam no checkpoint, mas fora da análise.

## Resultados

### 1. Iterações fixas: a memória é mais rápida

20 pares por busca local (4 instâncias × 5 seeds):

| busca local | qualidade (com vs sem) | tempo de parede (com vs sem) | tempo médio |
|---|---|---|---|
| original (varredura completa) | +0,025%, 6/4/10, p = 0,45 | **−23,8%**, 16/0/4 mais rápido, **p = 0,012** | 83,6 s → 70,0 s |
| `candidate-dlb` | +0,003%, 10/5/5, p = 0,30 | **−19,0%**, 18/0/2 mais rápido, **p = 0,0004** | 19,5 s → 16,2 s |

O efeito do grasp-am-large-scale **se confirma isolado**: não era a construção sem
`sort`, era a memória. E ele vale com as duas buscas locais.

**De onde vem o ganho** (por reinício, exceto o primeiro, que nunca tem memória;
busca local original):

| | sem memória | com memória |
|---|---:|---:|
| gap da solução construída | 233% | **64%** |
| gap após a 1ª descida | 7,4% | 3,4% |
| duração da 1ª descida | 38,6 ms | 28,0 ms |
| gap do ótimo do reinício | 0,66% | 0,52% |
| iterações de ILS por reinício | 320 | **236** |
| duração do reinício | 8,3 s | **6,8 s** |
| distância até a melhor solução global | 36% dos nós | **22%** |
| reinícios que voltam ao **mesmo** ótimo | 3% | **26%** |
| reinícios que melhoram a melhor solução global | 18% | 17% |

Com `candidate-dlb` o padrão é o mesmo: construção de 236% para 73%, 341 para 258
iterações por reinício, distância de 32% para 22%, repetições de 4% para 16%.

A economia **não** vem da descida mais barata, que pesa pouco no total. Ela vem de
**reinícios mais curtos**. Um reinício do ILS termina após `I_ILS` perturbações seguidas
sem melhora; partindo de uma solução já parecida com a melhor conhecida, há menos
melhoras pelo caminho, e o reinício acaba com ~25% menos iterações.

### 2. Tempo fixo, `I_ILS` = 300 (o método proposto): empate

30 pares:

| | sem memória | com memória |
|---|---:|---:|
| qualidade final | — | +0,004%, 14/9/7, p = 0,19 |
| reinícios por execução | 1,7 | 2,1 |
| gap do ótimo de cada reinício (exceto o 1º) | 0,68% | **0,30%** |
| distância até a melhor solução global | 42% | **23%** |
| reinícios que melhoram a melhor solução global | 33% | 39% |

Custo ao longo do tempo (rel%, com vs sem): −0,04% aos 5 s, +0,04% aos 10 s, −0,06%
aos 25 s, −0,15% aos 50 s (p = 0,064), −0,07% aos 75 s, +0,01% aos 100 s. Nada
significativo. Tempo até o alvo: o mesmo número de execuções atinge cada alvo (2%, 1%
e 0,5% acima da referência) com e sem memória, com medianas parecidas (54,5 s contra
58,4 s no alvo de 0,5%).

**A memória quase não age neste regime.** Com `I_ILS` = 300 e n ≥ 500, **19 das 30
execuções têm um único reinício**: o orçamento acaba durante o primeiro, e a memória,
que só é usada a partir do segundo, nunca entra. Nessas 19, os dois braços fazem
exatamente o mesmo reinício 0 (verificado: construção e primeira descida idênticas nos
30 pares), e as diferenças são só de ruído de tempo.

Restrito aos pares em que **os dois** braços chegaram a reiniciar (9 pares, em `att532`,
`rat783` e `d1291`), a memória fica **−0,113%** (7/1/1, p = 0,070). O recorte é
legítimo: como o reinício 0 é idêntico nos dois braços, "houve 2º reinício" é decidido
antes de a memória existir. Mas são 9 pares em 3 instâncias: é uma indicação, não uma
conclusão.

### 3. Tempo fixo, `I_ILS` = 30 (muitos reinícios): vantagem só no início

30 pares, ~18–21 reinícios por execução:

| t | rel% (com vs sem) | V/E/D | p |
|---:|---:|---:|---:|
| 5 s | −0,037 | 11/13/6 | 0,33 |
| **10 s** | **−0,290** | **20/6/4** | **0,0015** |
| 25 s | +0,147 | 12/2/16 | 0,57 |
| 50 s | −0,076 | 18/1/11 | 0,26 |
| 75 s | −0,167 | 19/1/10 | 0,14 |
| 100 s | −0,121 | 20/0/10 | 0,099 |

A vantagem aos 10 s é a única significativa e sobrevive a uma correção de Holm para as
12 comparações de tempo (p ajustado = 0,018). Ela coincide com o momento em que a
memória começa a agir: os primeiros reinícios a partir de padrões são curtos e já saem
bons. Daí em diante a vantagem oscila e não se sustenta.

No tempo até o alvo de 2% acima da referência, a mediana cai de 17,1 s para 8,2 s, mas
o teste pareado não é significativo (16/4/10, p = 0,33). Nos alvos de 1% e 0,5%, quase
nenhuma execução chega lá com `I_ILS` = 30, com ou sem memória.

**A memória não substitui a recalibração de `I_ILS`.** Com memória e `I_ILS` = 30, o
custo final fica **0,89% pior** que sem memória e `I_ILS` = 300 (1/0/29, p < 10⁻⁷). A
memória faz os reinícios "lembrarem" da melhor solução, o que poderia compensar
reinícios frequentes. Compensa um pouco (sem memória, a diferença é 1,01%), mas está
longe de compensar o efeito de simplesmente reiniciar menos.

### 4. Robustez

Desvio-padrão e pior caso por instância, a 100 s:

| instância | `I_ILS` = 30: dp sem → com | pior sem → com | `I_ILS` = 300: dp sem → com | pior sem → com |
|---|---:|---:|---:|---:|
| `att532` | 0,14 → 0,17 | 0,96 → 0,96 | 0,19 → 0,16 | 0,64 → **0,37** |
| `rat783` | 0,28 → 0,34 | 1,47 → 1,46 | 0,29 → 0,27 | 0,71 → 0,64 |
| `pr1002` | 0,30 → 0,21 | 2,32 → 2,46 | 0,53 → 0,51 | 1,36 → 1,36 |
| `pcb1173` | 0,36 → 0,50 | 2,62 → 2,70 | 0,86 → 0,83 | 2,20 → 2,20 |
| `d1291` | 0,91 → 0,79 | 2,67 → **2,15** | 0,44 → 0,72 | 1,10 → **1,98** |
| `nrw1379` | 0,35 → **0,15** | 2,01 → **1,47** | 0,19 → 0,18 | 0,43 → 0,43 |

(gap% para a referência.) Não há padrão: a memória reduz a variação em `nrw1379`
(`I_ILS` = 30) e o pior caso em `att532` (`I_ILS` = 300), mas aumenta os dois em
`d1291` (`I_ILS` = 300). Com 5 seeds por instância, essas diferenças estão dentro do
que se espera por acaso.

## Por que a memória não converte velocidade em qualidade

O mecanismo aparece inteiro nos rastros. A construção com memória soma a cada aresta um
bônus proporcional à frequência dela no pool de elite. Com o pool pequeno (os primeiros
reinícios), quase todas as arestas da melhor solução têm frequência alta, e a
construção **praticamente copia a melhor solução**. No piloto em `lin318`, o reinício 1
com memória construiu uma rota de custo 5 582 041, exatamente o ótimo do reinício 0, e
terminou no mesmo ótimo, à distância 0.

Isso tem dois efeitos opostos:

- **Eficiência:** o reinício parte de uma solução boa, termina mais cedo e já chega a
  um ótimo melhor (0,30% contra 0,68% com `I_ILS` = 300). É o ganho de 19–24% a
  iterações fixas.
- **Menos diversificação:** o reinício existe para levar a busca a outra região, e com
  a memória ele volta para perto de onde já estava (distância de 42% para 23%). Uma
  parte dos reinícios repete o ótimo conhecido (até 26%).

A tempo fixo os dois efeitos se cancelam. A memória faz mais reinícios (17,7 → 21,1 com
`I_ILS` = 30), mas cada um explora menos, e a fração de reinícios que melhora a melhor
solução quase não muda (12,8% → 13,5%). É o mesmo padrão de outras ideias do projeto
que mudam de onde a busca recomeça ([H1](h1-adaptive-diversification.md),
[H2](h2-elite-path-relinking.md), o *restart-kick* do H19): no MLP, recomeçar perto da
melhor solução não ajuda o ILS a encontrar outra melhor.

## Conclusão

1. **A memória adaptativa contribui em eficiência:** a orçamento de iterações fixo, ela
   entrega a mesma qualidade com 19–24% menos tempo, com significância e com as duas
   buscas locais.
2. **Ela não contribui em qualidade a tempo fixo**, que é o critério do método
   proposto. A eficiência vira reinícios, mas reinícios menos diversos.
3. **No método proposto (`I_ILS` = 300, n ≥ 500, 100 s), ela quase não tem oportunidade
   de agir**: na maioria das execuções há um só reinício. Onde age, há uma indicação de
   ganho (−0,11%, 7/1/1 em 9 pares), sem significância.
4. **Ela dá uma vantagem curta no início da busca** quando há muitos reinícios
   (`I_ILS` = 30, −0,29% aos 10 s), que não se sustenta.

**Para a dissertação:** a memória pode ser apresentada como um mecanismo de economia de
trabalho por reinício, com ganho de tempo medido e isolado. Não deve ser apresentada como
fonte de qualidade. Se o critério for qualidade a tempo fixo, o método poderia
dispensá-la sem perda (como o `gils_rvnd_dlb` do H19 e o braço sem memória da ablação
mostram). A favor de mantê-la: ela não custa nada em qualidade e economiza tempo quando
o critério de parada é por iterações.

## Limitações

1. **5 seeds por instância.** Suficiente para os efeitos de tempo (p ≤ 0,012) e para o
   empate em qualidade, mas não para efeitos de ~0,1%, como o −0,11% nos pares em que a
   memória agiu.
2. **Parâmetros da memória fixos** (λ = 0,5, pool = 20). Um λ menor reduziria a cópia
   da melhor solução e, talvez, a perda de diversidade; o irace do método não ajustou λ
   porque a ablação já indicava efeito nulo.
3. **Orçamento de 100 s em instâncias grandes.** Com orçamentos maiores, haveria mais
   reinícios e a memória teria mais oportunidades de agir.
4. **A `att532` ficou fora do protocolo de iterações fixas**, por custo.

## Onde está cada coisa

| o quê | onde |
|---|---|
| flag `--trace` | [`src/gils_am_rvnd.cpp`](../../src/gils_am_rvnd.cpp) |
| driver e relatório | [`scripts/am_study.py`](../../scripts/am_study.py) (`--suite iter` / `fixed100`) |
| dados (com os rastros) | [`results/am-study/iter.json`](../../results/am-study/iter.json), [`results/am-study/fixed100.json`](../../results/am-study/fixed100.json) |

Reproduzir o relatório:

```bash
python3 scripts/am_study.py --suite iter --out results/am-study/iter.json --report-only \
    --instances kroA200 a280 lin318 pr439
python3 scripts/am_study.py --suite fixed100 --out results/am-study/fixed100.json --report-only
```
