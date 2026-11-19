# Notas de leitura: Resende & Ribeiro sobre GRASP

Leitura de duas fontes, para a fundamentação teórica do TCC e para ideias futuras:

- **[RR16]** Resende, M.G.C., Ribeiro, C.C. (2016). *Optimization by GRASP: Greedy
  Randomized Adaptive Search Procedures*. Springer. DOI 10.1007/978-1-4939-6530-4.
  Arquivo local: `Downloads/Resende_Ribeiro-Optimization_by_GRASP.pdf` (323 p.).
  Bib: `resende2016`.
- **[RR19]** Resende, M.G.C., Ribeiro, C.C. (2019). Greedy Randomized Adaptive Search
  Procedures: Advances and Extensions. In: Gendreau, Potvin (eds.), *Handbook of
  Metaheuristics*, 3ª ed., Springer, pp. 169–220. DOI 10.1007/978-3-319-91086-4_6.
  Arquivo local: `Downloads/grasp-pr.pdf` (só as pp. 187–197, path-relinking).
  Bib: `resende2019`.

Os docs das hipóteses (`grasp-am-large-scale`, `h20`) não citavam fonte para a memória
adaptativa. A fonte canônica do esquema que o `gils_am_rvnd` implementa é
**Fleurent & Glover (1999)**, apresentado em [RR16, §7.6]. O termo vem de **Rochat &
Taillard (1995)**. As duas já estão no `.bib` do TCC (`fleurent1999`, `rochat1995`).

Seções lidas: RR16 §3.4, §4.3.3–4.3.4, §4.5.2, §5.1–5.4, §7.1, §7.6–7.8, §7.10, §9.1–9.2,
§9.5; RR19 §6.4–6.4.8.

---

## 1. O que já entrou no TCC (Cap. 4)

| conceito | fonte | onde entrou |
|---|---|---|
| construção semigulosa, LRC por qualidade (eq. com α) e por cardinalidade | RR16 §3.4, §5.2 | Seção GRASP, eq. `eq:lrc` |
| α = 0 guloso, α = 1 aleatório (minimização) | RR16 §5.2 | Seção GRASP |
| semigulosas: melhores que aleatórias, mais variadas que gulosas | RR16 §5.2, Fig. 5.3 | Seção GRASP |
| solução inicial melhor → caminho mais curto da busca local | RR16 §5.3, Figs. 5.8–5.10 | Seção GRASP |
| busca local domina o tempo na maioria das aplicações | RR16 §5.4 | Seção GRASP |
| listas de candidatos e busca circular | RR16 §4.3.3–4.3.4 | Seção Busca local |
| GRASP básico é sem memória | RR16 §9.1 | Seção Memória adaptativa |
| conjunto elite: entrada por qualidade e diversidade, saída da mais parecida | RR16 §7.6, §9.2; RR19 §6.4 | Seção Memória adaptativa |
| intensidade I(e), função composta K(e) = F(g(e), I(e)), peso λ | RR16 §7.6 (Fleurent & Glover 1999) | Seção Memória adaptativa |
| GRASP reativo, path-relinking, DM-GRASP | RR16 §7.1, §7.8; RR19 §6.4 | Seção Memória adaptativa |

## 2. Achados que conversam com os nossos resultados

**A memória do livro também acelera mais do que melhora.** No DM-GRASP para replicação
de servidores [RR16 §7.8, Tab. 7.2], a versão com padrões minerados melhora a melhor
solução em 12 de 20 instâncias e roda, em média, **36,8% mais rápido**. É o mesmo
padrão do H20: a memória adaptativa reduz o tempo em 19–24% sem mudar a qualidade.
Vale citar na discussão: o efeito de velocidade de construções guiadas por memória
aparece também na literatura de GRASP.

**O mecanismo da velocidade está no livro.** RR16 §5.3 mostra que a distância (Hamming)
entre a solução construída e o ótimo local se correlaciona com o número de movimentos e
com o tempo da busca local (Fig. 5.10). No H20, a memória faz a construção começar mais
perto da melhor solução, e o reinício fica mais curto. O argumento do H20 tem respaldo
direto aqui.

**A diversidade cai, como o livro prevê.** RR16 §7.6 descreve λ como controle entre
diversificação e intensificação. No H20, com λ = 0,5 a distância até a melhor solução
cai de 36% para 22% dos nós. É intensificação, exatamente o que o termo de memória
deveria fazer. A falta de ganho em qualidade a tempo fixo é coerente com isso: mais
reinícios, mas menos diversos.

**A busca local domina o tempo [RR16 §5.4].** Sustenta a abertura do Cap. 5 ("a busca
local concentra o custo computacional"). Hoje o Cap. 5 cita só `silva2012` ali.
**Sugestão:** acrescentar `\citep{resende2016}` nessa frase.

**Busca circular ≈ varredura contínua + DLB.** RR16 §4.3.4 descreve a busca circular:
depois de aplicar um movimento, a varredura recomeça do movimento seguinte, porque os
anteriores provavelmente continuam sem melhorar. O livro diz que isso acelera a busca
"em várias ordens de grandeza, sem perda de qualidade". É o mesmo raciocínio dos
*don't-look bits* e da varredura contínua do `candidate-dlb`. Bom para a Metodologia,
para situar o DLB numa ideia já consolidada.

**"Listas de candidatos" tem dois sentidos.** Em RR16 §4.3.3 é uma estratégia genérica:
reaproveitar os Δ da varredura anterior e só reavaliar os movimentos que eram de
melhora. No nosso trabalho (Toth & Vigo 2003), é a vizinhança granular: só os K
vizinhos mais próximos. O Cap. 4 usa o sentido amplo e cita o livro; a Metodologia deve
deixar claro que usamos o sentido granular, com `toth2003`.

## 3. Diferenças entre o nosso esquema e o de Fleurent & Glover

| aspecto | Fleurent & Glover / RR16 §7.6 | `gils_am_rvnd` |
|---|---|---|
| uso da memória | enviesa a **probabilidade de escolha** dentro da LRC: p(e) = K(e)/ΣK | altera o **custo** antes de formar a LRC: c'(u,v) = t_uv − λ·freq·avgDist |
| combinação | K(e) = λ·g(e) + I(e) (exemplo do livro) | bônus subtraído do custo, escalado pela distância média |
| λ | pode variar no tempo (Binato et al. 2002) | fixo em 0,5 |
| entrada no elite | qualidade **e** diversidade (diferença mínima δ) | só deduplicação e corte pelo custo (`AddElite`) |
| saída do elite | a mais parecida entre as não melhores | a pior |

A Metodologia deve apresentar o nosso esquema como **variante** do de Fleurent & Glover.
A memória entra no custo guloso, como nas perturbações de custo de RR16 §7.4, e não na
probabilidade de escolha.

## 4. Ideias para o futuro

1. **Elite com diversidade [RR16 §9.2].** Hoje o `AddElite` aceita qualquer solução
   melhor que a pior. A regra do livro (entrar só se diferir em pelo menos δ arcos e
   sair a mais parecida) ataca o problema que o H20 encontrou: memória sem diversidade.
   Barato de testar.
2. **λ variável [RR16 §7.6; Binato et al. 2002].** Começar com λ baixo (diversificação)
   e subir ao longo dos reinícios. Responde diretamente à queda de diversidade do H20.
3. **Escolha enviesada dentro da LRC [RR16 §7.5, Bresina 1996].** Em vez de sortear
   uniformemente, usar probabilidade por posição (linear, exponencial). Alternativa
   mais suave ao bônus no custo.
4. **GRASP reativo para α [RR16 §7.1; Prais & Ribeiro 2000].** O GILS-RVND sorteia α
   uniformemente em {0, 0,01, …, 0,25}. A versão reativa aprende os valores bons. Fácil
   de implementar.
5. **Princípio da otimalidade próxima [RR16 §7.7].** Aplicar busca local algumas vezes
   *durante* a construção. Com a busca local rápida do `candidate-dlb`, o custo seria
   pequeno.
6. **Filtragem [RR16 §5.4].** Só aplicar a busca local à melhor de η construções.
   Pouco relevante com I_ILS = 300 (poucos reinícios), mas útil no regime de muitos
   reinícios.
7. **Path-relinking misto ou truncado [RR19 §6.4.4–6.4.5].** O H2 testou o PR clássico
   e não achou efeito. O livro mostra que as melhores soluções ficam perto das
   extremidades do caminho (Fig. 6.13): explorar só 10–20% do caminho custa uma fração
   do tempo. O PR misto teve o melhor perfil de tempo (Fig. 6.12).
8. **Reinícios como estratégia de cauda [RR16 §9.5].** Reiniciar após um número fixo de
   iterações corta a cauda longa da distribuição do tempo até o alvo. Liga-se à
   discussão de I_ILS = 300 contra 100.

## 5. Figuras que podem entrar no TCC

| figura | inspiração | dados que já temos |
|---|---|---|
| **TTT plot** (distribuição empírica do tempo até atingir um alvo), com e sem memória | RR16 cap. 6; RR19 Figs. 6.10 e 6.12; Aiex et al. (2007) | `results/am-study/` (H20 mediu tempo até alvo de 2% e 0,5%) |
| custo da construção × custo do ótimo local, por reinício, com e sem memória | RR16 Figs. 5.8–5.9 | H20 (construção sai de 160% para 45% acima da referência com memória) |
| distância construção → ótimo local × número de movimentos da busca local | RR16 Fig. 5.10 | H20 (distância à melhor solução, 36% → 22%) |
| melhor e média em função de α | RR16 Fig. 5.7 | não temos; exigiria um lote variando α |
| exemplo didático do TSP em que o guloso falha e o semiguloso acerta (4 nós) | RR16 §3.4, Fig. 3.17 | figura conceitual, para o Cap. 4 |
| pseudocódigo do GRASP com conjunto elite | RR16 Fig. 9.1; RR19 Fig. 6.11 | o `docs/concepts/grasp-am.md` já tem os três algoritmos |

O **TTT plot** é a figura mais forte: é o instrumento padrão da literatura de GRASP para
comparar velocidade, e o resultado principal da memória adaptativa é de velocidade.

## 6. Referências novas no `.bib` do TCC

`resende2016`, `resende2019`, `fleurent1999`, `rochat1995`, `prais2000`, `laguna1999`,
`ribeiro2006`. Dados tirados da lista de referências de RR16 e, para RR19, da página
do capítulo no EconPapers/RePEc (pp. 169–220, DOI 978-3-319-91086-4_6).

Referências citadas aqui e ainda fora do `.bib`: Binato et al. (2002), *A GRASP for job
shop scheduling*, in Ribeiro & Hansen (eds.), *Essays and Surveys in Metaheuristics*,
pp. 59–79; Bresina (1996), *Heuristic-biased stochastic sampling*, AAAI-96; Aiex,
Resende & Ribeiro (2007), *TTTPLOTS*, Optimization Letters 1:355–366.
