# Revisão da literatura do MLP — base indexada para consulta

Base única sobre o Problema da Latência Mínima (MLP) e sobre as técnicas que o projeto
usou ou testou. Foi montada a partir de:

1. os três artigos de MLP em `docs/papers/`, lidos por inteiro, com as listas de
   referências;
2. todos os `.md` do repositório (`docs/`, `README.md`, `irace/`, `external/`);
3. uma busca na web, que só traz trabalhos posteriores a 2019.

**Como usar.**
- **Localizar:** cada trabalho tem um ID. O prefixo diz o tipo:
  - `L`: MLP e problemas próximos;
  - `T`: técnicas gerais de metaheurística e busca local;
  - `D`: mineração de dados em metaheurísticas;
  - `F`: ferramentas, estatística e instâncias;
  - `W`: achados da busca na web.
- **Detalhar:** a seção 2 é o índice e as seções seguintes dão os detalhes por tema.
- **Citar:** as referências completas estão na seção 11.

**Siglas de fonte**, que dizem de onde veio cada informação:

| sigla | fonte |
|---|---|
| SAL11 | `salehipour-2011-grasp-vnd-vns.pdf` (lido inteiro) |
| SIL12 | `silva-2012-gils-rvnd.pdf` (lido inteiro) |
| SAN19 | `santana-2019-mdm-gils-rvnd.pdf` (lido inteiro) |
| DOC:x | documento do projeto `x` (caminho relativo a `docs/`) |
| WEB | busca na web; o trabalho **não foi lido** |
| † | dado bibliográfico completado de memória, **não** confirmado num PDF ou doc do repositório; conferir antes de citar |

**Chave BibTeX:** quando o trabalho já está em `../tcc/Ref/SampleReferences.bib`, a
chave aparece entre crases.

---

## 1. O problema

### 1.1 Definição e nomes

- **Definição:** dado um depósito e `n` clientes com tempos de viagem entre eles,
  encontrar a ordem de visita que minimiza a **soma dos tempos de chegada** (latências)
  dos clientes.
- **Orientação ao cliente:** o TSP minimiza o tempo total do veículo, enquanto o MLP
  minimiza a espera de quem é atendido (SAL11, SIL12, SAN19).
- **Nomes alternativos:**
  - *Traveling Repairman Problem*, TRP (Tsitsiklis 1992; Afrati 1986);
  - *Delivery Man Problem* (Fischetti 1993);
  - *Traveling Deliveryman Problem* (Méndez-Díaz 2008; Mladenović 2013);
  - *Cumulative TSP* (Bianco 1993);
  - *School Bus Driver Problem* (Chaudhuri 2003).
- **Duas variantes:**
  - **circuito hamiltoniano:** a chegada de volta ao depósito entra na soma (SIL12,
    Tabela 1; SAN19, Tabela 1);
  - **caminho hamiltoniano:** sem retorno ao depósito (SAL11; SIL12, Tabelas 2 a 7).
    O GILS-RVND trata o caminho ignorando a latência do retorno (SAN19).
- **Forma por aresta:** em SAL11, `f(x) = Σ_{i=1..n} (n−i+1)·w(x_{i−1}, x_i)`. A aresta
  da posição `i` é paga por todos os clientes ainda não atendidos. É equivalente à soma
  das latências e é mais eficiente para avaliar inserções e remoções.

### 1.2 Por que é difícil

- **Complexidade:** NP-difícil em espaços métricos gerais (L01) e mesmo em árvores com
  pesos nas arestas (L12).
- **Não localidade:** a função objetivo é **não local**. Um arco no início afeta a
  latência de todos os vértices seguintes, e pequenas mudanças propagam alterações
  grandes na estrutura da solução ótima (Blum 1994; SIL12; SAN19).
- **Aproximação:** é muito mais difícil de aproximar que o TSP. A melhor razão métrica
  conhecida é 3,59 (L15), contra 1,5 no TSP métrico (Christofides 1976) (SAL11).
- **A solução do TSP não serve:** o tour ótimo do TSP avaliado pela função do MLP fica,
  em média, **16,9% pior** que a melhor solução de MLP encontrada, nas 10 TSPLIB
  selecionadas (SAL11, Tabela 9).
- **Problema-mãe:** o MLP e o TSP são casos especiais do *Time-Dependent TSP* (TDTSP),
  em que o custo de um arco depende da posição dele no circuito (SIL12, com Abeledo
  2010, Blum 1994 e Lucena 1990). O TDTSP e o MLP também são vistos como escalonamento
  em uma máquina com tempos de preparação dependentes da sequência (Bigras 2008; Gouveia
  e Voss 1995; Picard e Queyranne 1978), sob a medida *flow-time* (Tsitsiklis 1992)
  (SIL12).

### 1.3 Limitantes simples (SAL11, Seção 3)

- **Superior:** a heurística do vizinho mais próximo, como em Simchi-Levi e Berman (1991)
  e Bianco et al. (1993). É o GRASP de SAL11 com RCL de tamanho 1.
- **Inferior** (SAL11, Proposição 1): ordenar as arestas da árvore geradora mínima em
  ordem crescente e multiplicar a i-ésima por `(n−i+1)`. O intervalo entre os dois
  limitantes é grande, como esperado (Blum 1994).
- **Uso nos artigos:** SIL12 e SAN19 reportam o gap contra esse limitante superior nas
  instâncias aleatórias. É o "UB%" das tabelas.

---

## 2. Índice

### 2.1 MLP e problemas próximos (L)

| ID | trabalho | ano | categoria | conteúdo | fonte | bib |
|---|---|---|---|---|---|---|
| L01 | Sahni & Gonzalez | 1976 | complexidade | NP-dificuldade em espaços métricos gerais | SIL12, SAN19 | `sahni1976` |
| L02 | Picard & Queyranne | 1978 | relacionado | TDTSP aplicado a atraso em uma máquina | SIL12 | — |
| L03 | Afrati et al. | 1986 | complexidade | complexidade do TRP; casos polinomiais (caminhos) | SAL11, SIL12, SAN19 | — |
| L04 | Lucena | 1990 | exato | branch-and-bound com limitante lagrangiano; 15 a 30 nós | SIL12, SAN19 | — |
| L05 | Simchi-Levi & Berman | 1991 | limitante | vizinho mais próximo como limitante superior | SAL11 | — |
| L06 | Tsitsiklis | 1992 | variante | casos especiais com janelas de tempo; nome TRP | SIL12 | `tsitsiklis1992` |
| L07 | Fischetti, Laporte & Martello | 1993 | exato + heurística | enumerativo com limitantes de PLI (matroides cumulativos); até 60 vértices | SAL11, SIL12, SAN19 | `fischetti1993` |
| L08 | Bianco, Mingozzi & Ricciardelli | 1993 | exato | TSP com custos cumulativos; dois algoritmos com limitantes lagrangianos | SAL11, SIL12, SAN19 | — |
| L09 | Blum et al. | 1994 | aproximação | primeiro fator constante (144); polinomial em árvores de diâmetro ≤ 3 | SAL11, SIL12, SAN19 | `blum1994` |
| L10 | Van Eijl | 1995 | exato | formulação MIP (abordagem poliédrica) | SIL12, SAN19 | — |
| L11 | Gouveia & Voss | 1995 | formulação | classificação de formulações do TDTSP | SIL12 | — |
| L12 | Sitters | 2002 | complexidade | NP-difícil em árvores com pesos | SIL12 | — |
| L13 | Goemans & Kleinberg | 1998 | aproximação | razão melhorada | SIL12 | — |
| L14 | Ausiello, Leonardi & Marchetti-Spaccamela | 2000 | aproximação | vendedores, consertadores e aranhas | SIL12 | — |
| L15 | Chaudhuri et al. | 2003 | aproximação | fator 3,59 (métrico geral, o menor conhecido) | SAL11, SIL12, SAN19 | `chaudhuri2003` |
| L16 | Arora & Karakostas | 2003 | aproximação | esquemas de aproximação | SIL12 | — |
| L17 | Archer & Williamson | 2003 | aproximação | algoritmos mais rápidos | SIL12 | — |
| L18 | Wu | 2000 | exato | programação dinâmica; algoritmos polinomiais para casos especiais | SAL11 | — |
| L19 | García, Jodrá & Tejel | 2002 | complexidade | nota sobre o TRP; polinomial em caminhos | SAL11, SIL12 | — |
| L20 | Wu, Huang & Zhan | 2004 | exato | branch-and-bound; ~25 vértices em 100 s, mais rápido que o CPLEX numa formulação padrão | SAL11, SIL12 | — |
| L21 | Sarubbi & Luna | 2007 | formulação | formulação de fluxo para o MLP | SAL11 | — |
| L22 | Fakcharoenphol, Harrelson & Rao | 2007 | variante / aproximação | k-traveling repairmen (vários servidores) | SIL12 | — |
| L23 | Méndez-Díaz, Zabala & Lucena | 2008 | exato | nova formulação MIP; concluem que o TRP é muito difícil de resolver otimamente | SAL11, SIL12, SAN19 | `mendezdiaz2008` |
| L24 | Campbell, Vandenbussche & Hermann | 2008 | aplicação + heurística | roteamento para ajuda humanitária; heurísticas para MLP e TSP | SIL12, SAN19 | `campbell2008` |
| L25 | Bigras, Gamache & Savard | 2008 | exato / relacionado | TDTSP e escalonamento em uma máquina | SIL12 | — |
| L26 | Nagarajan & Ravi | 2008 | aproximação / variante | MLP direcionado (custos assimétricos) | SIL12 | — |
| L27 | Abeledo, Fukasawa, Pessoa & Uchoa | 2010a,b | exato | branch-cut-and-price com formulação estendida; até 107 vértices (23 TSPLIB) | SIL12, SAN19 | `abeledo2013` (versão de periódico de 2013) |
| L28 | Archer & Blasiak | 2010 | aproximação | fator 3,03 em árvores com pesos (*prize-collecting strolls*) | SIL12, SAN19 | — |
| L29 | Ezzine, Semet & Chabchoub | 2010 | exato + aplicação | duas formulações inteiras; até 29 vértices; recuperação de dados em redes | SIL12, SAN19 | — |
| L30 | Heilporn, Cordeau & Laporte | 2010 | variante | MLP com janelas de tempo; duas formulações e duas heurísticas (com e sem tabu) | SIL12, SAN19 | — |
| L31 | Ngueveu, Prins & Wolfler Calvo | 2010 | heurística | memético para o CCVRP (VRP capacitado cumulativo); limitantes para o MLP | SAL11, SIL12, SAN19 | — |
| L32 | Dewilde et al. | 2010 | variante | TRP com lucros; heurísticas (tabu) | SIL12 | — |
| L33 | Salehipour, Sörensen, Goos & Bräysy | 2011 | heurística | **primeira metaheurística** para o MLP: GRASP+VND e GRASP+VNS | SAL11, SIL12, SAN19 | `salehipour2011` |
| L34 | Silva, Subramanian, Vidal & Ochi | 2012 | heurística | **GILS-RVND**; estado da arte | SIL12, SAN19 | `silva2012` |
| L35 | Ribeiro & Laporte | 2012 | heurística (CCVRP) | ALNS para o CCVRP, não testado no MLP | SIL12 | — |
| L36 | Angel-Bello, Alvarez & García | 2012 | exato | duas formulações melhoradas; casos assimétricos | SAN19 | — |
| L37 | Mladenović, Urošević & Hanafi | 2013 | heurística | dois GVNS | SAN19 | `mladenovic2013` |
| L38 | Roberti & Mingozzi | 2014 | exato | *dynamic ng-path relaxation*; até 150 vértices | SAN19 | — |
| L39 | Rios | 2016 | heurística | busca local em CPU/GPU; GILS-RVND paralelo; fonte de BKS do S500 | SAN19 | — |
| L40 | Bulhões, Sadykov & Uchoa | 2018 | exato | branch-and-price com ng-path; ótimo provado até 195 vértices | SAN19, DOC | `bulhoes2018` |
| L41 | Santana, Plastino & Rosseti | 2019 | heurística | **MDM-GILS-RVND**; 32 novos BKS | SAN19, DOC | `santana2019` |
| L42 | Araujo, Coelho & Marzulo | 2020 | heurística | busca local *multi-improvement* com dataflow e GPU para o MLP | DOC:hypotheses/h4 | — |
| L43 | Tüű-Szabó, Földesi & Kóczy | 2020 | heurística | DBMEA (memético bacteriano) | DOC:hypotheses/h8, WEB | `tuuszabo2020` |
| L44 | Ren, Hao, Wu & Fu | 2023 | heurística (variante) | busca híbrida para o *multiple TRP with profits*; crossover ABX | DOC:concepts/method-explained, h19 | — |
| L45 | Jmal, Haddar & Chabchoub | 2025 | heurística | GQPSO (*Guided Quantum PSO*) para o MLP/TRP | DOC:hypotheses/h8, h11 | — |

### 2.2 Técnicas gerais (T)

| ID | trabalho | ano | técnica | uso no projeto | fonte |
|---|---|---|---|---|---|
| T01 | Croes | 1958 | 2-opt | vizinhança do GILS-RVND | TCC (`croes1958`) |
| T02 | Lin & Kernighan † | 1973 | Lin-Kernighan | H14: escape sequencial estilo LK | DOC:hypotheses/h14 (citado sem referência) |
| T03 | Or | 1976 | Or-opt | vizinhança do GILS-RVND; H12 | TCC (`or1976`) |
| T04 | Christofides | 1976 | aproximação 1,5 para o TSP métrico | comparação de aproximabilidade | SAL11 |
| T05 | Savelsbergh | 1985 | busca local com janelas de tempo; viabilidade em O(1) | origem da avaliação por concatenação | SIL12 |
| T06 | Feo & Resende | 1989, 1995 | GRASP | construção do GILS-RVND | SAL11, SIL12, SAN19 (`feo1995`) |
| T07 | Martin, Otto & Felten | 1991 | *double-bridge* / *large-step Markov chains* | perturbação do GILS-RVND | SIL12, SAN19, DOC |
| T08 | Bentley | 1992 | *don't-look bits* | componente da proposta (H19) | DOC:hypotheses/h19, concepts/method-explained |
| T09 | Kontoravdis & Bard | 1995 | GRASP para VRPTW | exemplo de GRASP em roteamento | SAL11 |
| T10 | Potts & van de Velde | 1995 | dynasearch | H10 | DOC:hypotheses/h10 |
| T11 | Mladenović & Hansen | 1997 | VNS | base do VND/RVND | SAL11, SIL12, SAN19 (`mladenovic1997`) |
| T12 | Kindervater & Savelsbergh | 1997 | trocas de arestas em roteamento; reotimização por concatenação | base da avaliação em O(1) do GILS-RVND | SIL12, SAN19 |
| T13 | Voudouris & Tsang | 1997 | Guided Local Search (GLS) | H11 | DOC:hypotheses/h11 |
| T14 | Shaw | 1998 | remoção por proximidade (*Shaw removal*) | H9c | DOC:hypotheses/h9 |
| T15 | Hansen & Mladenović | 1999, 2001a, 2001b | VNS: introdução, aplicações, princípios | — | SAL11 |
| T16 | Prais & Ribeiro | 2000 | Reactive GRASP | citado como não testado (H1) | DOC:hypotheses/h1 |
| T17 | Cordone & Wolfler Calvo | 2001 | VNS para VRPTW | exemplo de VNS em roteamento | SAL11 |
| T18 | Crispim & Brandão | 2001 | tabu reativo + VND para VRP com backhauls | exemplo de VND | SAL11 |
| T19 | Congram, Potts & van de Velde | 2002 | dynasearch iterado | H10 | DOC:hypotheses/h10 |
| T20 | Talbi | 2002 | taxonomia de metaheurísticas híbridas | contexto do MDM | SAN19 |
| T21 | Lourenço, Martin & Stützle | 2003 | Iterated Local Search | laço do GILS-RVND | SIL12, SAN19 (`lourenco2003`) |
| T22 | Ribeiro & Vianna | 2003 | GRASP + VND para filogenia | GRASP+VND antes do MLP | SAL11 |
| T23 | Toth & Vigo | 2003 | busca tabu granular (listas de candidatos) | componente da proposta (H16) | DOC:concepts/method-explained, proposal-vs-gils-rvnd |
| T24 | Bräysy & Gendreau | 2005 | metaheurísticas para VRPTW (survey) | múltiplas vizinhanças são a regra | SAL11 |
| T25 | Ropke & Pisinger | 2006 | ALNS / *ruin-and-recreate* | H9 | DOC:hypotheses/h1, h9 |
| T26 | Subramanian et al. | 2010 | RVND (heurística paralela para VRPSPD) | busca local do GILS-RVND | SIL12, SAN19 (`subramanian2010`) |
| T27 | Vidal, Crainic, Gendreau & Prins | 2011 (relatório), 2015 (*Networks*) | visão unificada de problemas de *timing* | extensão da avaliação por concatenação | SIL12, SAN19 |
| T28 | Benlic & Hao | 2013 | perturbação adaptativa para ILS | citado como não testado (H1) | DOC:hypotheses/h1 |
| T29 | XKICK | — | *kick* inteligente para o TSP | citado como não testado (H1) | DOC:hypotheses/h1 |
| T30 | Máximo & Nascimento | 2021 | AILS-PR (ILS adaptativo + path relinking, CVRP) | H1 (controle por distância), H2 | DOC:hypotheses/h1, h2 |
| T31 | Hudson et al. | 2022 | GNN-GLS (regret de arestas) | H5 | DOC:hypotheses/h5 |
| T32 | Máximo, Cordeau & Nascimento | 2024 | AILS-II (CVRP de grande porte) | referência de ILS adaptativo | DOC:hypotheses/h1 |
| T33 | Glover † | — | path relinking | H2 | DOC:hypotheses/h2 (citado sem referência) |

### 2.3 Mineração de dados em metaheurísticas (D)

| ID | trabalho | ano | conteúdo | fonte |
|---|---|---|---|---|
| D01 | Agrawal & Srikant | 1994 | Apriori | SAN19 |
| D02 | Han, Pei & Yin | 2000 | FP-Growth | SAN19 |
| D03 | Grahne & Zhu | 2003 | FPMax* (itemsets frequentes maximais) | SAN19, DOC:hypotheses/h13 |
| D04 | Ribeiro, Trindade, Plastino & Martins | 2004 | DM-GRASP (*set packing*) | SAN19 |
| D05 | Santos, Ribeiro, Plastino & Martins | 2005 | DM-GRASP para o *maximum diversity problem* | SAN19 |
| D06 | Ribeiro, Plastino & Martins | 2006 | DM-GRASP (periódico) | SAN19 |
| D07 | Santos et al. | 2006 | DM-GRASP para *server replication* | SAN19 |
| D08 | Han, Kamber & Pei | 2011 | livro de mineração de dados | SAN19 |
| D09 | Plastino et al. | 2011 | MDM-GRASP (*p*-mediana) | SAN19 |
| D10 | Barbalho, Rosseti, Martins & Plastino | 2013 | DM-GRASP + path relinking (2-path network design) | SAN19 |
| D11 | Plastino et al. | 2014 | versões adaptativas e multi-mining do DM-GRASP | SAN19 |
| D12 | Maia | 2015 | dissertação: heurísticas híbridas com mineração para VRP de frota heterogênea | SAN19 |
| D13 | Guerine, Rosseti & Plastino | 2016 | mineração de **arcos** para permutações (*one-commodity pickup-and-delivery TSP*) | SAN19 |
| D14 | Yun, Lee & Lee | 2016 | mineração de padrões representativos | SAN19 |
| D15 | Martins et al. | 2018 | "Making a state-of-the-art heuristic faster with data mining" | SAN19 |
| D16 | MDM-HGS-CVRP (Maia) | — | código de referência da integração FPmax + HGS | DOC:hypotheses/h13, external/fpmax |

### 2.4 Ferramentas, estatística e instâncias (F)

| ID | trabalho | conteúdo | fonte |
|---|---|---|---|
| F01 | Reinelt (1991) | TSPLIB | SIL12, DOC:concepts/distance-types |
| F02 | Siegel & Castellan (1988) | estatística não paramétrica (Wilcoxon) | SAN19 |
| F03 | Aiex, Resende & Ribeiro (2007) | gráficos *time-to-target* (TTT) | SAN19 |
| F04 | Dongarra (2011) | fatores de desempenho entre computadores (escala de tempo) | SIL12 |
| F05 | López-Ibáñez et al. † (2016) | irace | DOC:irace/README, benchmarks/irace-dlb-tuning |
| F06 | FIMI | repositório de implementações de mineração de itemsets frequentes | SAN19, DOC:hypotheses/h13 |
| F07 | FPmax-LIB | FPMax* de Grahne & Zhu como biblioteca (MIT) | DOC:hypotheses/h13, external/fpmax |
| F08 | Santana, Plastino & Rosseti (2018) | dados experimentais do MDM (Mendeley) | SAN19 |
| F09 | Garey & Johnson † (1979) | teoria da NP-completude; referência clássica para as classes P, NP e NP-difícil | nenhuma fonte do repositório (acrescentado a pedido) |

### 2.5 Achados da busca na web (W)

| ID | trabalho | ano | o que relata | observação |
|---|---|---|---|---|
| W01 | busca local determinística paralela (*Cluster Computing*) | 2020 | "novas melhores soluções" em eil51, berlin52, pr107, rat195, pr226 | **suspeito**: essas instâncias têm ótimo provado; provavelmente outra variante ou arredondamento |
| W02 | Mikula et al., *Traveling Delivery Person* | 2022 | 4 novos BKS em instâncias de 500 clientes; GILS-RVND ainda um pouco melhor em parte | não lido |
| W03 | DBMEA com inicialização *Circle Group Heuristic* (*Symmetry* 17(10):1683; capítulo Springer) | 2025–2026 | melhores soluções nas instâncias maiores | não lido |
| W04 | ROAR (arXiv) | — | 2-opt restrito + *ruin-and-recreate* para TRP de grande escala | **não confirmado** que exista |

---

## 3. Complexidade, formulações e métodos exatos

### 3.1 Complexidade e casos polinomiais
- **NP-difícil:** em espaço métrico geral (L01) e em árvores com pesos (L12). Para a
  definição das classes P, NP e NP-difícil, a referência clássica é Garey e Johnson
  (F09). Os três artigos não a citam: provam ou citam a NP-dificuldade direto por L01.
- **Polinomial:** em caminhos (L03, L19), em árvores não ponderadas e em árvores de
  diâmetro até 3 (L09, L19, L20) (SAL11, SIL12).

### 3.2 Métodos exatos

| ID | método | maior instância resolvida |
|---|---|---|
| L04 Lucena 1990 | branch-and-bound + lagrangiano | 15–30 nós |
| L07 Fischetti 1993 | enumerativo + limitantes de PLI (matroides) | 60 |
| L08 Bianco 1993 | dois algoritmos com limitantes lagrangianos | — |
| L10 Van Eijl 1995 | MIP | — |
| L18 Wu 2000 | programação dinâmica | — |
| L20 Wu 2004 | branch-and-bound | ~25 em 100 s |
| L21 Sarubbi 2007 | formulação de fluxo | — |
| L23 Méndez-Díaz 2008 | MIP + branch-and-cut | — |
| L29 Ezzine 2010 | duas formulações inteiras | 29 |
| L30 Heilporn 2010 | duas formulações (com janelas de tempo) | — |
| L27 Abeledo 2010 | branch-cut-and-price | **107** |
| L36 Angel-Bello 2012 | formulações para o caso assimétrico | — |
| L38 Roberti & Mingozzi 2014 | geração de colunas + ng-path dinâmico | **150** |
| L40 Bulhões 2018 | branch-and-price + ng-path | **195** |

- **CPLEX no MLP, segundo SAL11 (Tabelas 3 e 4):**
  - com 10 clientes, acha o ótimo das 20 instâncias em 162 s em média;
  - com 20 clientes, não prova otimalidade em 24 h: o gap médio é 53% após 1 h e 25%
    após 24 h.
  - O GRASP+VNS acha as mesmas soluções em menos de 0,02 s, e melhores em 2 casos.
- **Ótimos usados como referência:** SIL12 rodou o código do BCP de Abeledo, cedido
  pelos autores, para obter os ótimos das instâncias aleatórias de até 50 clientes.
  Antes, SAL11 só tinha ótimos até 20 clientes.
- **Leitura geral:** os métodos exatos não resolvem de forma consistente instâncias com
  mais de ~100 a 200 clientes (SIL12, SAN19), o que justifica as metaheurísticas.

### 3.3 Aproximação

| ID | fator | domínio |
|---|---|---|
| L09 Blum 1994 | 144 | métrico (primeiro fator constante) |
| L15 Chaudhuri 2003 | **3,59** | métrico geral |
| L28 Archer & Blasiak 2010 | 3,03 | árvores com pesos nas arestas |
| L13, L14, L16, L17, L26 | — | outras aproximações citadas por SIL12 |

---

## 4. Metaheurísticas para o MLP, em detalhe

### 4.1 L33 — Salehipour et al. (2011), GRASP+VND e GRASP+VNS (SAL11)

**Contexto:** é a primeira metaheurística para o MLP. Antes dela só havia métodos
exatos e aproximações. A versão é a do **caminho**, e as distâncias são arredondadas
para baixo.

**Construção (GRASP):**
- A RCL tem os **α vértices mais próximos** do último inserido, um número fixo e não
  uma fração.
- O vértice é escolhido ao acaso na RCL. Usa uma matriz de proximidade pré-computada.
- **α = 2** foi o melhor no estudo piloto.
- Motivação: as primeiras arestas pesam mais, então o guloso tende a ir bem.

**Vizinhanças**, na ordem de exploração:
1. **swap-adjacent**, O(n);
2. **remove-insert**, O(n): para cada `x_i`, move o vértice mais distante dele para o
   final da rota. É própria do artigo;
3. **swap**, O(n²);
4. **2-opt**, O(n²);
5. **Or-opt**, O(n³): blocos de 1 a 3 numa vizinhança só.

O desempenho é pouco sensível à ordem das vizinhanças. Cada uma é explorada com
**melhor melhoria**.

**VND e VNS:**
- O VNS perturba **antes de cada vizinhança** (*shaking*): retira 20% dos clientes e os
  reinsere em posições aleatórias.
- Não recentra na melhor solução depois do *shaking*, ao contrário do VNS padrão.

**Reduções de vizinhança:**
- **Fix:** fixa um vértice aleatório e testa só movimentos que o envolvem, o que reduz
  a vizinhança por um fator O(n). O oposto é NoFix, a vizinhança completa.
- **Fator de proximidade β:** limita a distância, na rota, entre os vértices de um
  movimento. "Full" usa β = n, ou 250 para n ≥ 500; "Half" usa β = n/2, ou 300/200/100
  para swap/2-opt/Or-opt quando n ≥ 500.
- Com essas duas opções, mais *single-start* contra *multi-start* (10 construções), o
  artigo testa **8 configurações**.

**Instâncias:**
- 140 aleatórias, 20 por tamanho n ∈ {10, 20, 50, 100, 200, 500, 1000};
- coordenadas uniformes em [0, 100] até n = 200 e em [0, 500] para 500 e 1000;
- "disponíveis com os autores, sob pedido";
- mais **10 TSPLIB**: st70, rat99, kroD100, lin105, pr107, rat195, pr226, lin318,
  pr439, att532.

**Máquina:** Pentium 4, 2,4 GHz, 512 MB, C++.

**Resultados:**
- *Multi-start* custa muito mais tempo e ganha pouco.
- A perturbação do VNS ajuda um pouco.
- As duas reduções são úteis em n = 500 e 1000.

**Lacunas apontadas pelos autores:** mais vizinhanças, estudo do efeito de cada uma,
variantes com vários veículos, ganho de eficiência e integração com métodos exatos.

**No projeto:** reimplementado em `src/grasp_vnd.cpp` (DOC:hypotheses/h-salehipour).
O gerador de instâncias foi corrigido para os intervalos da Tabela 1 do artigo.
Estender o Or-opt até 6 melhora o GRASP+VND em 0,34% nas 140 instâncias (p < 0,001).

### 4.2 L34 — Silva et al. (2012), GILS-RVND (SIL12)

**Algoritmo:**
- Multi-start com `I_max` iterações. Cada uma faz:
  1. construção GRASP com α sorteado em R;
  2. ILS, que repete RVND + perturbação até `I_ILS` perturbações seguidas sem melhora.
- A perturbação é sempre aplicada à melhor solução da iteração (`s'`).
- Parâmetros: `I_max = 10`, `I_ILS = min(100, n)`, `R = {0,00, 0,01, …, 0,25}`.

**Construção:** ordena os candidatos pela distância ao último inserido. A RCL tem os α%
melhores (uma fração). Com α = 0, ou com RCL vazia, é o vizinho mais próximo.

**RVND:**
- Ordem aleatória das vizinhanças, que nos testes preliminares foi melhor que a ordem
  fixa.
- Melhor melhoria, varredura exaustiva.
- Cinco vizinhanças: swap, 2-opt, reinserção, or-opt2 e or-opt3.

**Perturbação:** *double-bridge* (T07), uma permutação de dois segmentos disjuntos.

**Avaliação em O(1) amortizado** (Proposição 1), a segunda contribuição do artigo:
- **Origem:** vem da reotimização por concatenação de Kindervater e Savelsbergh (T12),
  estendida por Vidal et al. (T27), e da ideia de Savelsbergh (T05).
- **Dados por subsequência:** cada subsequência σ guarda a duração `T`, o custo `C` e o
  custo de atraso `W`, que é o número de clientes:
  - `T(σ⊕σ') = T(σ) + t + T(σ')`
  - `C(σ⊕σ') = C(σ) + W(σ')·(T(σ) + t) + C(σ')`
  - `W(σ⊕σ') = W(σ) + W(σ')`
- **Custo:** pré-processamento em O(n²); cada movimento é a concatenação de no máximo 5
  subsequências.

**Máquina:** Core i7 2,93 GHz, 8 GB, g++ 4.4.3, Ubuntu 10.04, um núcleo. O tempo de
Salehipour foi escalado pelos fatores de Dongarra (F04).

**Resultados**, em 9 conjuntos e **173 instâncias** de 10 a 1000 clientes:

| conjunto | resultado |
|---|---|
| 23 TSPLIB de Abeledo (42–107, circuito) | ótimo em **todas as execuções**; novos melhores em `rat99` e `eil101` (sem ótimo provado); 0,16 a 12,76 s |
| 10 TSPLIB de Salehipour (caminho) | iguala ou melhora todos os melhores conhecidos; gap médio de **−2,34%** contra Salehipour (sem `att532`) |
| aleatórias, n = 10, 20, 50 | ótimo em todas as execuções; 0,01, 0,02 e 0,55 s |
| aleatórias, n = 100, 200, 500, 1000 | gap contra o vizinho mais próximo de −13,00%, −14,35%, −15,16% e −15,47% |

Na Tabela 8, o GILS-RVND supera o GRASP+VNS de Salehipour e o memético de Ngueveu
(L31) em quase todos os tamanhos, com menor tempo escalado.

**Futuro, segundo os autores:** variantes com lucros e com vários veículos.

**No projeto:** implementado em `src/gils_rvnd.cpp` e reproduz a qualidade publicada
(DOC:concepts/mlp-overview, benchmarks/mdm-paper-table1-reproduction).

### 4.3 L37 — Mladenović, Urošević & Hanafi (2013)

- **Método:** dois GVNS, com estratégias de busca local diferentes.
- **Instâncias:** as de Abeledo e de Salehipour.
- **Comparação:** só com Abeledo e Salehipour, sem comparar direto com o GILS-RVND.
  Pelos resultados publicados, o GILS-RVND é melhor (SAN19).

### 4.4 L39 — Rios (2016)

- **O que é:** tese da UFF sobre busca local em CPU/GPU, com versões paralelas baseadas
  no GILS-RVND.
- **Uso no SAN19:** é a fonte de parte dos BKS das instâncias de 500 e 1000 clientes
  (marcados com † nas Tabelas 2 e 3 do SAN19).

### 4.5 L41 — Santana, Plastino & Rosseti (2019), MDM-GILS-RVND (SAN19)

**Ideia:** hibridiza o GILS-RVND com mineração de dados no estilo MDM-GRASP (D09, D11).
Os padrões frequentes do conjunto elite guiam a construção.

**Duas fases:**
1. **Primeira metade das `I_max` iterações:** é o GILS-RVND puro, que mantém um
   conjunto elite D de tamanho d. A função `UpdateEliteSet` é chamada **dentro** do
   laço do ILS.
2. **Segunda metade:** antes de cada iteração, re-minera se D mudou. Usa um padrão para
   a construção híbrida.

**Mineração:**
- Cada solução elite vira uma transação de **arcos**, como em Guerine et al. (D13).
- O FPMax* (D03) extrai os itemsets frequentes maximais.
- Os `MaxP` maiores padrões viram listas de arcos consecutivos (*Consecutive Arc
  Lists*).

**Construção híbrida** (Algoritmo 5): igual à do GILS-RVND, mas quando o candidato
sorteado é o início de um segmento minerado, insere o segmento inteiro.

**Por que adaptar o MDM-GRASP:** o MDM-GRASP clássico re-minera quando o elite
estabiliza. Com só 10 iterações isso não acontece, porque os trabalhos anteriores
usavam 200 a 1000 iterações (D10, D11, D13). Os autores também criaram um
DM-GILS-RVND, de fase única, mas o MDM foi melhor.

**Parâmetros:**
- `sup_min = 70%`: melhor equilíbrio entre qualidade e tempo; os 20% usuais deixam a
  mineração cara demais;
- `d = 10`;
- `MaxP = 5`;
- o resto é igual ao GILS-RVND.

**Protocolo:**
- O GILS-RVND foi **reexecutado com o código original**, cedido por Silva et al., com
  as mesmas sementes e compilador.
- Máquina: Core i7 3,40 GHz, 16 GB, g++ 4.4.3, Ubuntu 14.04, um núcleo.
- 10 execuções por instância.
- Teste por instância pareado e unicaudal: t de Student se Shapiro-Wilk aceita
  normalidade, senão Wilcoxon. Nível de 5%.

**Resultados:**

| conjunto | resultado |
|---|---|
| 23 TSPLIB de Abeledo (circuito) | os dois acham os ótimos; médias iguais em 20; MDM 5,48% mais rápido |
| **56 TSPLIB, n de 120 a 1379 (circuito)**, novo conjunto | médias: MDM melhor em 30, GILS em 11; melhores: 49 contra 40; tempo −23,36%; 7 instâncias significativas a favor do MDM e 1 a favor do GILS; os dois atingem todos os ótimos de Bulhões (18 instâncias já testadas lá) |
| 10 TSPLIB de Salehipour (caminho) | mesmas melhores soluções (9 são BKS); gap médio de 0,08% (MDM) e 0,09% (GILS); MDM 14,47% mais rápido |
| aleatórias, n = 10, 20, 50 | idênticas e ótimas, em menos de 1 s |
| aleatórias, n = 100 e 200 | mesmas melhores (todas BKS); MDM 10,41% e 21,18% mais rápido |
| aleatórias, n = 500 | melhores: 15 contra 5; médias: 18 contra 2; gap ao BKS de 0,41% contra 0,51%; tempo −27,74% |
| aleatórias, n = 1000 | melhores: 19 de 20; médias: 20 de 20; tempo −32,78%; 10 significativas |

**Análises complementares (Seção 5.3):**
1. **Padrões:** em TRP-S500-R17, a construção com padrões cai drasticamente de custo, e
   cada padrão tem cerca de **480 arcos frequentes**.
2. **Gráficos TTT** (F03): o MDM chega ao alvo com mais probabilidade no mesmo tempo
   (kroA200, pr299 e TRP-S500-R17).
3. **Tempo como critério de parada** (Seção 5.3.3): o mais rápido dos dois roda pelo
   tempo do mais lento. Nas 56 TSPLIB, o MDM fica melhor em 51 resultados. No S500 e no
   S1000, o MDM melhora mais: no S1000 vence nas 20 instâncias e os 20 melhores superam
   os BKS.

**32 novos BKS** (Tabela 4), todos na **variante caminho**: `att532` (5 572 131), 11
instâncias S500 e 20 instâncias S1000.

**Futuro:** usar os padrões para reduzir o tamanho do problema, contraindo segmentos
em vértices (D12).

**Dados:** os logs estão no Mendeley (F08).

**No projeto:**
- **Implementação:** `src/mdm_gils_rvnd.cpp`, com FPMax* em C++ (FPmax-LIB) e defaults
  iguais aos do artigo (DOC:hypotheses/h13).
- **Reprodução nas 28 instâncias da Tabela 1 com n ≤ 318:** a qualidade bate com a do
  paper (diferença média de +0,0072%); a **redução de tempo não** (−1,1% contra
  −15,2%) (DOC:benchmarks/mdm-paper-table1-reproduction).
- **Causa provável:** o GILS-RVND original reconstrói estruturas n × n a cada
  movimento.

### 4.6 L42 — Araujo, Coelho & Marzulo (2020)

- **Método:** busca local *multi-improvement* com dataflow e GPU para o MLP. Aplica de
  uma vez vários movimentos de melhora com *footprints* disjuntos.
- **No projeto (H4):** a oportunidade existe, com ~1,8 a ~3,3 movimentos simultâneos
  por vizinhança, mas em CPU o modo `multi` ficou 1,3 a 2,3 vezes mais lento. Refutada
  (DOC:hypotheses/h4).

### 4.7 L43 — Tüű-Szabó, Földesi & Kóczy (2020), DBMEA

- **Método:** algoritmo memético bacteriano, com mutação bacteriana, transferência de
  genes e passo memético de busca local.
- **Resultados relatados:** iguala nas instâncias pequenas e médias; em n = 500 fica
  +0,35% melhor; em n = 1000, +0,40% a +0,57% melhor e ~1,9 vez mais rápido que o
  GILS-RVND (DOC:hypotheses/h8). Em parte das instâncias de 500 nós não supera o
  GILS-RVND (WEB).
- **No projeto (H8, DBMEA-lite):** não bateu o GILS-RVND em qualidade em lin318, att532
  e rand1000; em rand1000 o GILS-RVND fica ~2,7 a 2,9% melhor. O DBMEA-lite é mais
  rápido. A escala de tempo do artigo, de horas, não foi testada.

### 4.8 L45 — Jmal, Haddar & Chabchoub (2025), GQPSO

- **Método:** *Guided Quantum PSO* para o MLP/TRP. O componente de intensificação é um
  Guided Local Search (T13).
- **Resultados relatados:** mostra o mesmo padrão do DBMEA, com ganho nas instâncias
  grandes (DOC:hypotheses/h8).
- **No projeto (H11):** um GLS sobre o RVND ficou ~1,6% pior que o GILS-RVND em lin318
  (DOC:hypotheses/h11).

### 4.9 L44 — Ren, Hao, Wu & Fu (2023)

- **Método:** busca híbrida para o *multiple traveling repairman problem with profits*,
  publicada no EJOR (304(2), 381–394). É a origem do crossover baseado em arcos (ABX).
- **No projeto (H19):** o ABX entre soluções elite piorou em +0,26% (DOC:hypotheses/h19,
  reports/local-search-speedup-report).

### 4.10 Linha do tempo e estado da arte
1. **Antes de 2011:** poucas heurísticas, a maioria para variantes (L07, L24, L30, L31,
   L32).
2. **2011:** GRASP+VND e GRASP+VNS (L33), a primeira metaheurística para o MLP.
3. **2012:** GILS-RVND (L34), que passa a ser o estado da arte.
4. **2013:** GVNS (L37). **2016:** GILS-RVND paralelo (L39).
5. **2019:** MDM-GILS-RVND (L41), que melhora o GILS-RVND em qualidade e tempo,
   sobretudo com n ≥ 500.
6. **2020 a 2025:** DBMEA (L43), multi-improvement em GPU (L42) e GQPSO (L45) relatam
   ganhos nas instâncias grandes. Além deles há os itens da busca na web (W01 a W04).

**Leitura:** em 2019 o GILS-RVND é chamado de "state-of-the-art heuristic" (SAN19).
Depois disso, há trabalhos que dizem superá-lo nas instâncias grandes (L43, L45, W03),
mas nenhum foi lido na íntegra pelo projeto.

---

## 5. Variantes do problema

| variante | trabalhos |
|---|---|
| janelas de tempo | L06 Tsitsiklis 1992; L30 Heilporn 2010 |
| custos assimétricos / direcionado | L26 Nagarajan & Ravi 2008; L36 Angel-Bello 2012 |
| vários servidores (k-TRP) | L22 Fakcharoenphol 2007 |
| com lucros | L32 Dewilde 2010; L44 Ren 2023 (vários servidores com lucros) |
| capacitada / demanda cumulativa (CCVRP) | L31 Ngueveu 2010; L35 Ribeiro & Laporte 2012 |
| caminho × circuito | L33 usa caminho; L34 e L41 resolvem os dois |
| TDTSP (problema-mãe) | L02, L11, L25, L27 |

---

## 6. Aplicações

| aplicação | referência | fonte |
|---|---|---|
| entregas domiciliares / de mercadorias | L23 Méndez-Díaz 2008; L07 Fischetti 1993 | SIL12, SAN19 |
| logística humanitária / emergências | L24 Campbell 2008 | SIL12, SAN19 |
| recuperação de dados em redes | L29 Ezzine 2010 | SIL12, SAN19 |
| escalonamento de cabeça de disco | L09 Blum 1994 | SAL11, SAN19 |
| médico visitando pacientes; técnico consertando máquinas | — | SAL11 |
| sistemas de serviço do ponto de vista do cliente | Archer & Williamson 2003 (L17) | SIL12 |

---

## 7. Instâncias, melhores conhecidos e convenções

| conjunto | tamanho | variante | origem | usado em |
|---|---|---|---|---|
| TSPLIB de Abeledo | 23 instâncias, n de 42 a 107 (inclui `pr76r`) | circuito | L27 | SIL12, L37, SAN19; projeto (22, sem `pr76r`) |
| aleatórias de Salehipour (TRP-S*n*-R*x*) | 140 = 7 tamanhos × 20 | caminho | L33 | SIL12, L37, SAN19 (**não públicas**; o projeto as regerou) |
| TSPLIB de Salehipour | 10, n de 70 a 532 | caminho | L33 | SIL12 (Tab. 2), SAN19 |
| TSPLIB de Santana | 56, n de 120 a 1379 (`dsj1000` e `dsj1000ceil`) | circuito | L41 | SAN19 (Tab. 1); projeto (55, sem a `dsj1000` EUC_2D) |
| total SIL12 / SAN19 | 173 / 229 (79 circuito + 150 caminho) | — | — | — |

- **Ótimos e BKS:**
  - ótimos do circuito até 195 vértices: Bulhões 2018 (L40), 18 das 56 de Santana;
  - ótimos do caminho até 50 clientes: SIL12, rodando o BCP de Abeledo;
  - BKS do S500 e do S1000: SIL12 (*), Rios 2016 (†) e os 32 novos de SAN19.
- **Distância** (DOC:concepts/distance-types):
  - no **caminho** a literatura **trunca** `EUC_2D` (SAL11: "rounded down");
  - no **circuito** usa o `nint` do TSPLIB (Abeledo, Bulhões, SIL12 Tab. 1, SAN19 Tab. 1);
  - o projeto reproduz os BKS publicados com essas convenções.
- **TSPLIB:** Reinelt (1991) (F01).

---

## 8. Técnicas gerais e o que o projeto concluiu sobre elas

| técnica (ID) | o que é | resultado no projeto | doc |
|---|---|---|---|
| GRASP (T06) | construção gulosa aleatorizada + busca local, multi-start | base do GILS-RVND | concepts/method-explained |
| ILS (T21) + double-bridge (T07) | perturba o ótimo local e repete | base; variantes adaptativas (H1) nulas | hypotheses/h1 |
| VND / RVND (T11, T26) | várias vizinhanças; RVND sorteia a ordem | base | concepts/mlp-overview |
| avaliação por concatenação (T05, T12, T27) | custo de movimento em O(1) | base; a proposta troca as matrizes n × n por somas de prefixo O(n) (2,4 a 2,9 vezes mais rápido) | hypotheses/h16 |
| listas de candidatos / vizinhança granular (T23) | só movimentos que criam aresta para os K vizinhos mais próximos | **componente principal da proposta** (K = 12) | hypotheses/h16, concepts/proposal-vs-gils-rvnd |
| *don't-look bits* (T08) | um bit por cidade; só reexamina o que mudou | **componente da proposta** | hypotheses/h19 |
| Or-opt estendido (T03) | blocos de 4 a 6 e invertidos | **componente da proposta**; ganho cresce com n | hypotheses/h12 |
| 3-opt genuíno | reversão dupla independente | nulo (H12b) | hypotheses/h12b |
| Lin-Kernighan (T02) | cadeias sequenciais de 2-opt | empate, +30% de tempo (H14) | hypotheses/h14 |
| dynasearch (T10, T19) | combinação ótima de movimentos disjuntos por PD | refutada no diagnóstico (H10) | hypotheses/h10 |
| multi-improvement (L42) | vários movimentos disjuntos de uma vez | mais lento em CPU (H4) | hypotheses/h4 |
| GLS (T13) | penaliza arestas da solução | ~1,6% pior (H11) | hypotheses/h11 |
| perturbação por regret (T31) | corta o double-bridge onde o regret é alto | refutada (H5) | hypotheses/h5 |
| ruin-and-recreate / ALNS (T25, T14) | remove k clientes e reinsere por regret | perde para o double-bridge (H9) | hypotheses/h9 |
| path relinking (T33, T30) | caminhos entre soluções elite | nulo (H2) | hypotheses/h2 |
| diversificação adaptativa (T30, T16, T28, T29) | força da perturbação por estagnação ou distância | nula (H1) | hypotheses/h1 |
| algoritmo memético (L43) | população + mutação + busca local | não bate o GILS-RVND (H8) | hypotheses/h8 |
| crossover ABX (L44) | recombina arcos de elites | +0,26% pior (H19) | hypotheses/h19 |
| memória adaptativa | bônus por frequência de arestas no elite, na construção | só velocidade (−19% a −24%), não qualidade | hypotheses/grasp-am-large-scale, h20 |
| mineração de padrões (MDM, L41) | itemsets frequentes maximais de arcos | nulo em qualidade no projeto (H13) | hypotheses/h13 |
| construção com lookahead (L07 como inspiração) | rollout guloso de k passos | ajuda a construção, some com o RVND (H6) | hypotheses/h6 |

**Conclusão do projeto** (DOC:hypotheses/h19, reports/local-search-speedup-report): no
MLP, mudar *de onde* a busca recomeça (perturbação, recombinação, memória, mineração)
não sobrevive ao RVND. O que melhora o resultado é vizinhança e velocidade da busca
local.

---

## 9. Mineração de dados em metaheurísticas (contexto do MDM)

- **DM-GRASP** (D04, D06): um GRASP em duas fases separadas por uma mineração.
  1. A primeira fase guarda as d melhores soluções.
  2. A mineração extrai itemsets frequentes com suporte ≥ `sup_min`.
  3. A segunda fase constrói cada solução a partir de um padrão, escolhido em
     *round-robin*, e completa com a construção original. A busca local não muda.
- **Melhor variante:** a de itemsets frequentes **maximais**.
- **Aplicações:** *maximum diversity* (D05), *server replication* (D07), *p*-mediana
  (D09), *2-path network design* (D10) e *one-commodity PDTSP* (D13).
- **MDM-GRASP** (D09, D11): re-minera sempre que o elite estabiliza, ou seja, fica
  algumas iterações sem mudar. Os padrões vão se refinando, e o resultado foi melhor que
  o DM-GRASP em qualidade e tempo.
- **Permutações** (D13): minerar **arcos** `(i, j)` em vez de vértices preserva a
  ordem.
- **Algoritmos de mineração:** Apriori (D01), FP-Growth (D02) e FPMax* (D03). Este
  último ainda é considerado estado da arte, ao lado do MAFIA e do LCM (D14).
- **Hibridização em geral:** taxonomia de Talbi (T20) e livro de Han et al. (D08).

---

## 10. Pontos de atenção

- **Bulhões et al. (2018):** SAN19 diz que o algoritmo resolve até **195 vértices**. O
  TCC usa "cerca de 200".
- **Abeledo et al.:** os artigos citam os relatórios de 2010 (a, b). O `.bib` do TCC usa
  a versão de periódico de 2013 (`abeledo2013`), que não está nos artigos.
- **Lourenço et al. (2003):** SIL12 dá as páginas 320–353; o `.bib` do TCC tem 321–353.
- **Tüű-Szabó et al. (2020):** o doc H8 dá *IJCIS* 13(1), 781–793; o `.bib` do TCC está
  sem páginas.
- **Angel-Bello et al.:** SAN19 cita o ano 2012 com o volume 37 de *Applied Mathematical
  Modelling*, que é de 2013.
- **32 novos BKS do SAN19:** são do **caminho**, não do circuito. Os 12 novos BKS do
  projeto são do circuito, contra a Tabela 1 do SAN19 (DOC:benchmarks/literature-comparison).
- **W01** relata "novos BKS" em instâncias com ótimo provado. Não usar sem ler o artigo.
- **Itens † e WEB:** os dados bibliográficos e os números deles não foram conferidos
  num PDF.

---

## 11. Referências completas

Em ordem alfabética. A etiqueta final diz de onde veio a referência.

- Abeledo, H., Fukasawa, R., Pessoa, A., Uchoa, E. (2010a). The Time Dependent Traveling Salesman Problem: polyhedra and algorithm. Tech. Rep. RPEP vol. 10 no. 15, Universidade Federal Fluminense. [SIL12, SAN19]
- Abeledo, H., Fukasawa, R., Pessoa, A., Uchoa, E. (2010b). The time dependent traveling salesman problem: polyhedra and branch-cut-and-price algorithm. In: *SEA 2010*, pp. 202–213. [SIL12, SAN19]
- Abeledo, H., Fukasawa, R., Pessoa, A., Uchoa, E. (2013). The time dependent traveling salesman problem: polyhedra and algorithm. *Mathematical Programming Computation* 5(1), 27–55. † [`.bib` do TCC]
- Afrati, F., Cosmadakis, S., Papadimitriou, C.H., Papageorgiou, G., Papakostantinou, N. (1986). The complexity of the traveling repairman problem. *RAIRO Informatique Théorique et Applications* 20, 79–87. [SAL11, SAN19]
- Agrawal, R., Srikant, R. (1994). Fast algorithms for mining association rules in large databases. In: *VLDB 1994*, pp. 487–499. [SAN19]
- Aiex, R.M., Resende, M.G.C., Ribeiro, C.C. (2007). TTT plots: a perl program to create time-to-target plots. *Optimization Letters* 1, 355–366. [SAN19]
- Angel-Bello, F., Alvarez, A., García, I. (2012/2013). Two improved formulations for the minimum latency problem. *Applied Mathematical Modelling* 37, 2257–2266. [SAN19]
- Araujo, Coelho, Marzulo (2020). A multi-improvement local search using dataflow and GPU to solve the minimum latency problem. [DOC:hypotheses/h4; periódico não informado]
- Archer, A., Blasiak, A. (2010). Improved approximation algorithms for the minimum latency problem via prize-collecting strolls. In: *SODA 2010*, pp. 429–447. [SIL12, SAN19]
- Archer, A., Williamson, D.P. (2003). Faster approximation algorithms for the minimum latency problem. In: *SODA 2003*, pp. 88–96. [SIL12]
- Arora, S., Karakostas, G. (2003). Approximation schemes for minimum latency problems. *SIAM Journal on Computing* 32(5), 1317–1337. [SIL12]
- Ausiello, G., Leonardi, S., Marchetti-Spaccamela, A. (2000). On salesmen, repairmen, spiders, and other traveling agents. In: *CIAC 2000*, pp. 1–16. [SIL12]
- Barbalho, H., Rosseti, I., Martins, S.L., Plastino, A. (2013). A hybrid data mining GRASP with path-relinking. *Computers & Operations Research* 40, 3159–3173. [SAN19]
- Benlic, U., Hao, J.-K. (2013). A study of adaptive perturbation strategy for iterated local search. In: *EvoCOP 2013*, LNCS 7832. [DOC:hypotheses/h1]
- Bentley, J.L. (1992). Fast algorithms for geometric traveling salesman problems. *ORSA Journal on Computing* 4(4), 387–411. [DOC:hypotheses/h19, concepts/method-explained]
- Bianco, L., Mingozzi, A., Ricciardelli, S. (1993). The traveling salesman problem with cumulative costs. *Networks* 23(2), 81–91. [SAL11, SIL12, SAN19]
- Bigras, L.-P., Gamache, M., Savard, G. (2008). The time-dependent traveling salesman problem and single machine scheduling problems with sequence dependent setup times. *Discrete Optimization* 5(4), 685–699. [SIL12]
- Blum, A., Chalasani, P., Coppersmith, D., Pulleyblank, B., Raghavan, P., Sudan, M. (1994). The minimum latency problem. In: *STOC 1994*, pp. 163–171. [SAL11, SIL12, SAN19]
- Bräysy, O., Gendreau, M. (2005). Vehicle routing problem with time windows, part II: metaheuristics. *Transportation Science* 39, 119–139. [SAL11]
- Bulhões, T., Sadykov, R., Uchoa, E. (2018). A branch-and-price algorithm for the minimum latency problem. *Computers & Operations Research* 93, 66–78. [SAN19]
- Campbell, A.M., Vandenbussche, D., Hermann, W. (2008). Routing for relief efforts. *Transportation Science* 42(2), 127–145. [SIL12, SAN19]
- Chaudhuri, K., Godfrey, B., Rao, S., Talwar, K. (2003). Paths, trees, and minimum latency tours. In: *FOCS 2003*, pp. 36–45. [SAL11, SIL12, SAN19]
- Christofides, N. (1976). Worst-case analysis of a new heuristic for the travelling salesman problem. Tech. Rep. 388, Carnegie-Mellon University. [SAL11]
- Congram, R.K., Potts, C.N., van de Velde, S.L. (2002). An iterated dynasearch algorithm for the single-machine total weighted tardiness scheduling problem. *INFORMS Journal on Computing* 14(1), 52–67. † [DOC:hypotheses/h10 cita só os autores e o ano]
- Cordone, R., Wolfler Calvo, R. (2001). A heuristic for the vehicle routing problem with time windows. *Journal of Heuristics* 7, 107–129. [SAL11]
- Crispim, J., Brandão, J. (2001). Reactive tabu search and variable neighbourhood descent applied to the vehicle routing problem with backhauls. In: *MIC 2001*, pp. 631–636. [SAL11]
- Croes, G.A. (1958). A method for solving traveling-salesman problems. *Operations Research* 6(6), 791–812. † [`.bib` do TCC]
- Dantzig, G.B., Ramser, J.H. (1959). The truck dispatching problem. *Management Science* 6(1), 80–91. † [`.bib` do TCC]
- Dewilde, T., Cattrysse, D., Coene, S., Spieksma, F.C.R., Vansteenwegen, P. (2010). Heuristics for the traveling repairman problem with profits. In: *ATMOS 2010*, pp. 34–44. [SIL12]
- Dongarra, J.J. (2011). Performance of various computers using standard linear equations software. Tech. Rep. CS-89-85, University of Tennessee. [SIL12]
- Ezzine, I.O., Semet, F., Chabchoub, H. (2010). New formulations for the traveling repairman problem. In: *MOSIM 2010*, pp. 1889–1894. [SIL12, SAN19]
- Fakcharoenphol, J., Harrelson, C., Rao, S. (2007). The k-traveling repairmen problem. *ACM Transactions on Algorithms* 3(4), 40. [SIL12]
- Feo, T.A., Resende, M.G.C. (1989). A probabilistic heuristic for a computationally difficult set covering problem. *Operations Research Letters* 8, 67–71. [SAL11]
- Feo, T.A., Resende, M.G.C. (1995). Greedy randomized adaptive search procedures. *Journal of Global Optimization* 6(2), 109–133. [SAL11, SIL12, SAN19]
- Fischetti, M., Laporte, G., Martello, S. (1993). The delivery man problem and cumulative matroids. *Operations Research* 41(6), 1055–1064. [SAL11, SIL12, SAN19]
- Garey, M.R., Johnson, D.S. (1979). *Computers and Intractability: A Guide to the Theory of NP-Completeness*. W. H. Freeman, San Francisco. † [acrescentado a pedido; não está nas fontes do repositório]
- García, A., Jodrá, P., Tejel, J. (2002). A note on the traveling repairman problem. *Networks* 40(1), 27–31. [SAL11, SIL12]
- Goemans, M.X., Kleinberg, J.M. (1998). An improved approximation ratio for the minimum latency problem. *Mathematical Programming* 82(1), 111–124. [SIL12]
- Gouveia, L., Voss, S. (1995). A classification of formulations for the (time-dependent) traveling salesman problem. *European Journal of Operational Research* 83(1), 69–82. [SIL12]
- Grahne, G., Zhu, J. (2003). Efficiently using prefix-trees in mining frequent itemsets. In: *IEEE ICDM Workshop on Frequent Itemset Mining Implementations (FIMI)*, pp. 236–245. [SAN19]
- Guerine, M., Rosseti, I., Plastino, A. (2016). Extending the hybridization of metaheuristics with data mining: dealing with sequences. *Intelligent Data Analysis* 20, 1133–1156. [SAN19]
- Han, J., Kamber, M., Pei, J. (2011). *Data Mining: Concepts and Techniques*, 3ª ed. Morgan Kaufmann. [SAN19]
- Han, J., Pei, J., Yin, Y. (2000). Mining frequent patterns without candidate generation. In: *SIGMOD 2000*, pp. 1–12. [SAN19]
- Hansen, P., Mladenović, N. (1999). An introduction to variable neighborhood search. In: Voss et al. (eds.), *Meta-Heuristics*, Kluwer, pp. 433–458. [SAL11]
- Hansen, P., Mladenović, N. (2001a). Industrial applications of the variable neighbourhood search metaheuristic. In: *Decisions and Control in Management Science*, Kluwer, pp. 261–274. [SAL11]
- Hansen, P., Mladenović, N. (2001b). Variable neighbourhood search: principles and applications. *European Journal of Operational Research* 130, 449–467. [SAL11]
- Heilporn, G., Cordeau, J.-F., Laporte, G. (2010). The delivery man problem with time windows. *Discrete Optimization* 7(4), 269–282. [SIL12, SAN19]
- Hudson, B., Li, Q., Malencia, M., Prorok, A. (2022). Graph neural network guided local search for the traveling salesperson problem. *ICLR 2022*. † [DOC:hypotheses/h5 cita só "Hudson et al. (2022) — GNN-GLS"]
- Jmal, Haddar, Chabchoub (2025). GQPSO (Guided Quantum PSO) para o MLP/TRP. [DOC:hypotheses/h8, h11; dados completos não informados]
- Kindervater, G., Savelsbergh, M. (1997). Vehicle routing: handling edge exchanges. In: Aarts, Lenstra (eds.), *Local Search in Combinatorial Optimization*, Wiley, pp. 337–360. [SIL12, SAN19]
- Kontoravdis, G.A., Bard, J.F. (1995). A GRASP for the vehicle routing problem with time windows. *INFORMS Journal on Computing* 7, 10–23. [SAL11]
- Lin, S., Kernighan, B.W. (1973). An effective heuristic algorithm for the traveling-salesman problem. *Operations Research* 21(2), 498–516. † [DOC:hypotheses/h14 cita o método sem referência]
- López-Ibáñez, M., Dubois-Lacoste, J., Pérez Cáceres, L., Birattari, M., Stützle, T. (2016). The irace package: iterated racing for automatic algorithm configuration. *Operations Research Perspectives* 3, 43–58. † [DOC:irace/README cita só o site]
- Lourenço, H.R., Martin, O.C., Stützle, T. (2003). Iterated local search. In: Glover, Kochenberger (eds.), *Handbook of Metaheuristics*, Kluwer, pp. 320–353. [SIL12, SAN19]
- Lucena, A. (1990). Time-dependent traveling salesman problem — the deliveryman case. *Networks* 20(6), 753–763. [SIL12, SAN19]
- Maia, M.R.d.H. (2015). *Heurísticas híbridas com mineração de dados para o problema de roteamento de veículos com frota heterogênea*. Dissertação de mestrado, UFF. [SAN19]
- Martin, O., Otto, S.W., Felten, E.W. (1991). Large-step Markov chains for the traveling salesman problem. *Complex Systems* 5(3), 299–326. [SIL12, SAN19, DOC:hypotheses/h1]
- Martins, D., Vianna, G., Rosseti, I., Martins, S.L., Plastino, A. (2018). Making a state-of-the-art heuristic faster with data mining. *Annals of Operations Research* 263, 141–162. [SAN19]
- Máximo, V.R., Cordeau, J.-F., Nascimento, M.C.V. (2024). AILS-II: an adaptive iterated local search heuristic for the large-scale capacitated vehicle routing problem. *INFORMS Journal on Computing* 36(4), 974–986. arXiv:2205.12082. [DOC:hypotheses/h1]
- Máximo, V.R., Nascimento, M.C.V. (2021). A hybrid adaptive iterated local search with diversification control to the capacitated vehicle routing problem. *European Journal of Operational Research* 294, 1108–1119. arXiv:2012.11021. [DOC:hypotheses/h1]
- Méndez-Díaz, I., Zabala, P., Lucena, A. (2008). A new formulation for the traveling deliveryman problem. *Discrete Applied Mathematics* 156(17), 3223–3237. [SAL11, SIL12, SAN19]
- Mladenović, N., Hansen, P. (1997). Variable neighborhood search. *Computers & Operations Research* 24(11), 1097–1100. [SAL11, SIL12, SAN19, DOC:hypotheses/h1]
- Mladenović, N., Urošević, D., Hanafi, S. (2013). Variable neighborhood search for the travelling deliveryman problem. *4OR* 11, 57–73. [SAN19]
- Nagarajan, V., Ravi, R. (2008). The directed minimum latency problem. In: *APPROX/RANDOM 2008*, pp. 193–206. [SIL12]
- Ngueveu, S.U., Prins, C., Wolfler Calvo, R. (2010). An effective memetic algorithm for the cumulative capacitated vehicle routing problem. *Computers & Operations Research* 37(11), 1877–1885. [SAL11, SIL12, SAN19]
- Or, I. (1976). *Traveling salesman-type combinatorial problems and their relation to the logistics of regional blood banking*. Tese de doutorado, Northwestern University. † [`.bib` do TCC]
- Picard, J.-C., Queyranne, M. (1978). The time-dependent traveling salesman problem and its application to the tardiness problem in one-machine scheduling. *Operations Research* 26(1), 86–110. [SIL12]
- Plastino, A., Barbalho, H., Santos, L.F.M., Fuchshuber, R., Martins, S.L. (2014). Adaptive and multi-mining versions of the DM-GRASP hybrid metaheuristic. *Journal of Heuristics* 20, 39–74. [SAN19]
- Plastino, A., Fonseca, E.R., Fuchshuber, R., Freitas, A.A., Luis, M., Martins, S.L. (2011). A hybrid data mining metaheuristic for the p-median problem. *Statistical Analysis and Data Mining* 4, 313–335. [SAN19]
- Potts, C.N., van de Velde, S.L. (1995). Dynasearch — iterative local improvement by dynamic programming. Part I: the traveling salesman problem. Tech. Rep., University of Twente. † [DOC:hypotheses/h10 cita só os autores e o ano]
- Prais, M., Ribeiro, C.C. (2000). Reactive GRASP: an application to a matrix decomposition problem in TDMA traffic assignment. *INFORMS Journal on Computing* 12(3). [DOC:hypotheses/h1]
- Reinelt, G. (1991). TSPLIB — a traveling salesman problem library. *ORSA Journal on Computing* 3(4), 376–384. [SIL12]
- Ren, J., Hao, J.-K., Wu, F., Fu, Z.-H. (2023). An effective hybrid search algorithm for the multiple traveling repairman problem with profits. *European Journal of Operational Research* 304(2), 381–394. [DOC:concepts/method-explained]
- Ribeiro, C.C., Vianna, D.S. (2003). A GRASP/VND heuristic for the phylogeny problem using a new neighborhood structure. Tech. Rep., PUC-Rio. [SAL11]
- Ribeiro, G.M., Laporte, G. (2012). An adaptive large neighborhood search heuristic for the cumulative capacitated vehicle routing problem. *Computers & Operations Research* 39(3), 728–735. [SIL12]
- Ribeiro, M.H., Plastino, A., Martins, S.L. (2006). Hybridization of GRASP metaheuristic with data mining techniques. *Journal of Mathematical Modelling and Algorithms* 5, 23–41. [SAN19]
- Ribeiro, M.H., Trindade, V.A., Plastino, A., Martins, S.L. (2004). Hybridization of GRASP metaheuristics with data mining techniques. In: *ECAI Workshop on Hybrid Metaheuristics*, pp. 69–78. [SAN19]
- Rios, E. (2016). *Exploração de estratégias de busca local em ambientes CPU/GPU*. Tese de doutorado, UFF. [SAN19]
- Roberti, R., Mingozzi, A. (2014). Dynamic ng-path relaxation for the delivery man problem. *Transportation Science* 48, 413–424. [SAN19]
- Ropke, S., Pisinger, D. (2006). An adaptive large neighborhood search heuristic for the pickup and delivery problem with time windows. *Transportation Science* 40(4), 455–472. † (periódico) [DOC:hypotheses/h1, h9]
- Sahni, S., Gonzalez, T. (1976). P-complete approximation problems. *Journal of the ACM* 23(3), 555–565. [SIL12, SAN19]
- Salehipour, A., Sörensen, K., Goos, P., Bräysy, O. (2011). Efficient GRASP+VND and GRASP+VNS metaheuristics for the traveling repairman problem. *4OR* 9(2), 189–209. doi:10.1007/s10288-011-0153-0. [SAL11]
- Santana, Í., Plastino, A., Rosseti, I. (2018). Experimental data from "Improving a state-of-the-art heuristic for the minimum latency problem with data mining". Mendeley Data, doi:10.17632/sxz37ssdbc.2. [SAN19]
- Santana, Í., Plastino, A., Rosseti, I. (2019). Improving a state-of-the-art heuristic for the minimum latency problem with data mining. arXiv:1908.10705. [SAN19]
- Santos, L.F., Milagres, R., Albuquerque, C.V., Martins, S.L., Plastino, A. (2006). A hybrid GRASP with data mining for efficient server replication for reliable multicast. In: *IEEE Globecom 2006*, pp. 1–6. [SAN19]
- Santos, L.F.M., Ribeiro, M.H., Plastino, A., Martins, S.L. (2005). A hybrid GRASP with data mining for the maximum diversity problem. In: *Hybrid Metaheuristics 2005*, pp. 116–127. [SAN19]
- Sarubbi, J., Luna, H. (2007). A new flow formulation for the minimum latency problem. In: *INOC 2007*, Spa, Bélgica. [SAL11]
- Savelsbergh, M. (1985). Local search in routing problems with time windows. *Annals of Operations Research* 4(1), 285–305. [SIL12]
- Shaw, P. (1998). Using constraint programming and local search methods to solve vehicle routing problems. In: *CP-98*, LNCS 1520. [DOC:hypotheses/h9]
- Siegel, S., Castellan, N. (1988). *Nonparametric Statistics for the Behavioral Sciences*. McGraw-Hill. [SAN19]
- Silva, M.M., Subramanian, A., Vidal, T., Ochi, L.S. (2012). A simple and effective metaheuristic for the minimum latency problem. *European Journal of Operational Research* 221(3), 513–520. doi:10.1016/j.ejor.2012.03.044. [SIL12]
- Simchi-Levi, D., Berman, O. (1991). Minimizing the total flow time of n jobs on a network. *IIE Transactions* 23(3), 236–244. [SAL11]
- Sitters, R. (2002). The minimum latency problem is NP-hard for weighted trees. In: *IPCO 2002*, pp. 230–239. [SIL12]
- Subramanian, A., Drummond, L.M.A., Bentes, C., Ochi, L.S., Farias, R. (2010). A parallel heuristic for the vehicle routing problem with simultaneous pickup and delivery. *Computers & Operations Research* 37(11), 1899–1911. [SIL12, SAN19]
- Talbi, E.G. (2002). A taxonomy of hybrid metaheuristics. *Journal of Heuristics* 8, 541–564. [SAN19]
- Toth, P., Vigo, D. (2003). The granular tabu search and its application to the vehicle-routing problem. *INFORMS Journal on Computing* 15(4), 333–346. [DOC:concepts/method-explained]
- Toth, P., Vigo, D. (2014). *Vehicle Routing: Problems, Methods, and Applications*, 2ª ed. SIAM. † [`.bib` do TCC]
- Tsitsiklis, J.N. (1992). Special cases of traveling salesman and repairman problems with time windows. *Networks* 22(3), 263–282. [SIL12]
- Tüű-Szabó, B., Földesi, P., Kóczy, L.T. (2020). An efficient evolutionary metaheuristic for the traveling repairman (minimum latency) problem. *International Journal of Computational Intelligence Systems* 13(1), 781–793. doi:10.2991/ijcis.d.200529.001. [DOC:hypotheses/h8, WEB]
- Van Eijl, C.A. (1995). A polyhedral approach to the delivery man problem. Tech. Rep. COSOR 95-19, Eindhoven University of Technology. [SIL12, SAN19]
- Vidal, T., Crainic, T.G., Gendreau, M., Prins, C. (2011). A unifying view on timing problems and algorithms. Tech. Rep., CIRRELT. [SIL12]
- Vidal, T., Crainic, T.G., Gendreau, M., Prins, C. (2015). Timing problems and algorithms: time decisions for sequences of activities. *Networks* 62, 102–128. [SAN19]
- Voudouris, C., Tsang, E. (1997). Guided local search. [DOC:hypotheses/h11 cita só os autores e o ano]
- Wu, B.Y. (2000). Polynomial time algorithms for some minimum latency problems. *Information Processing Letters* 75, 225–229. [SAL11]
- Wu, B.Y., Huang, Z.-N., Zhan, F.-J. (2004). Exact algorithms for the minimum latency problem. *Information Processing Letters* 92(6), 303–309. [SAL11, SIL12]
- Yun, U., Lee, G., Lee, K.M. (2016). Efficient representative pattern mining based on weight and maximality conditions. *Expert Systems* 33, 439–462. [SAN19]
- FIMI — Frequent Itemset Mining Implementations repository. http://fimi.uantwerpen.be/src [SAN19, DOC:hypotheses/h13]
- FPmax-LIB. https://github.com/marcelorhmaia/FPmax-LIB [DOC:hypotheses/h13]
- MDM-HGS-CVRP. https://github.com/marcelorhmaia/MDM-HGS-CVRP [DOC:hypotheses/h13]
- XKICK — an intelligent kick perturbation for the traveling salesman problem. https://www.researchgate.net/publication/317370678 [DOC:hypotheses/h1]
