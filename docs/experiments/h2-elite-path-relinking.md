# H2 — Path relinking entre elites

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

Status: **ENCERRADA — sintoma real (mas distinto do enunciado original),
mecanismo testado não melhora o GILS-RVND.** Lote noturno com poder
estatístico real (seção 10: N=20/15/10 em `lin318`/`pr439`/`att532`) fecha o
veredito: efeito indistinguível de ruído em toda instância (p ≥ 0,30 em
todas; magnitude média sempre < 0,1%). **Não adotar.**

## 1. Hipótese

Se boas soluções são encontradas ao longo da busca e depois descartadas
(GILS-RVND mantém apenas o melhor global entre as `I_max`
reinicializações), então manter um pool de soluções elite e explorar os
caminhos entre elas (path relinking) recuperaria qualidade que o ILS puro
descarta. Sintoma que a justifica: soluções boas aparecem (em reinícios
diferentes) e não são reaproveitadas.

## 2. Diagnóstico do sintoma (antes de implementar qualquer coisa)

Usando o trace `-v` de `gils_rvnd` (ver
[h1-adaptive-diversification.md](h1-adaptive-diversification.md) seção 2),
rodamos GILS-RVND com os parâmetros padrão do artigo (`--imax 10 --iils
100`) e extraímos, de cada uma das até 10 iterações externas, a solução
final daquele reinício — as soluções que o algoritmo descarta ao ficar só
com o `s*` global.

Para cada instância, com as ~10 soluções finais de reinício, medimos
`spread%` (diferença entre pior e melhor), `near2` (quantas ficam a ≤2% da
melhor) e `mean_jacc` (similaridade média de Jaccard das arestas dirigidas
entre a melhor solução e as demais — o quanto são estruturalmente
parecidas, não só parecidas em custo).

| instância | n | reinícios válidos | spread% | soluções a ≤2% | mean_jacc (arestas) |
|---|---|---|---|---|---|
| eil51 | 51 | 10 | 2.27 | 9/10 | 0.798 |
| st70 | 70 | 10 | 0.00 | 10/10 | 0.963 |
| pr76 | 76 | 10 | 0.63 | 10/10 | 0.718 |
| kroA100 | 100 | 10 | 0.78 | 10/10 | 0.855 |
| lin105 | 105 | 10 | 0.00 | 10/10 | 1.000 |
| pr226 | 226 | 10 | 0.25 | 10/10 | 0.931 |
| lin318 | 318 | 10 | 0.97 | 10/10 | 0.438 |
| pr439 | 439 | 4 | 1.17 | 4/4 | 0.316 |

Dois achados coexistem:

1. **Em quase toda instância, os reinícios convergem para custo muito
   parecido** (spread ≤ 2,3%, quase sempre todos os reinícios a ≤2% do
   melhor). O "descarte" quase nunca joga fora uma solução *muito* pior.
2. **A similaridade estrutural (Jaccard de arestas) cai visivelmente nas
   duas maiores instâncias testadas** (`lin318`: 0.438, `pr439`: 0.316)
   frente às menores (tipicamente 0.7–1.0). Soluções de qualidade quase
   idêntica compartilham menos da metade dos arcos em instâncias maiores —
   caminhos bem diferentes chegando a custo parecido.

**Interpretação do diagnóstico**: o sintoma de H2 aparece, mas de forma
diferente do enunciado original — não é que soluções muito melhores sejam
descartadas (spread é pequeno em toda instância), é que aparecem múltiplas
soluções *estruturalmente distintas* de qualidade equivalente à medida que
`n` cresce, e apenas uma é aproveitada. Esse é o cenário clássico onde path
relinking tende a compensar. A tendência é sugestiva mas estatisticamente
fraca (só 2 pontos grandes, o segundo com poucos reinícios válidos).

## 3. Implementação

Mudança em [`src/gils_rvnd.cpp`](../../src/gils_rvnd.cpp), aditiva
(comportamento padrão idêntico sem a nova flag):

- `EliteEntry` / `add_elite`: pool de soluções elite (só tour + custo, não
  as matrizes O(n²) de reotimização — elas nunca ficam paradas no pool sem
  uso), com deduplicação por igualdade exata de rota. Segue o mesmo
  `AddElite` já esboçado em `algorithms/grasp_am.md` (ordena por custo,
  descarta a pior quando excede `--elite-size`, padrão 5).
- `path_relink(start, guideTour)`: path relinking clássico por troca
  posicional (Glover). Percorre as posições de `start` da esquerda para a
  direita; onde `start` difere de `guideTour`, troca o elemento atual pelo
  elemento que `guideTour` pede (usando um mapa de posições para achar onde
  ele está em `start`), recalcula o custo, e guarda o melhor ponto visto no
  caminho inteiro (incluindo os extremos). `O(n)` passos × `O(n²)` de
  reotimização por passo = `O(n³)` por chamada — mas só roda uma vez por
  reinício externo (`I_max` vezes no total), não dentro do laço ILS interno,
  então o custo total é desprezível mesmo em instâncias grandes (confirmado
  experimentalmente: overhead <1% em `lin318`).
- Integração no laço principal de `gils_rvnd`: ao final de cada reinício
  externo, se `--path-relinking` estiver ativo e o pool não estiver vazio,
  escolhe **um membro aleatório do pool** como guia, faz o path relinking a
  partir da solução daquele reinício, aplica `RVND` no melhor ponto do
  caminho para polir, e substitui a solução do reinício se o resultado for
  melhor. Em seguida adiciona a solução do reinício ao pool.
- Novas flags de CLI: `--path-relinking` (padrão desligado), `--elite-size`
  (padrão 5). Saída agora imprime `PATH_RELINKING on|off`.

## 4. Um erro no desenho do teste (e a correção)

Na primeira rodada do teste A/B (seção 5), usamos `--imax 1` para `pr439` e
`--imax 1` para `att532` por custo computacional — exatamente como fizemos
em outros diagnósticos desta sessão. **Isso invalida o teste nessas duas
instâncias**: o pool de elite começa vazio a cada execução, e só recebe seu
primeiro membro *depois* que o único reinício (`imax=1`) termina. Como não
há um segundo reinício para relinkar contra esse primeiro membro, o path
relinking **nunca chega a executar** com `imax=1` — o "empate exato em
100% das seeds" que a primeira rodada mostrou ali não é evidência de que o
mecanismo não ajuda, é evidência de que o mecanismo nunca rodou.

Reexecutamos `pr439` (`--imax 3`, 2 chances reais de path relinking por
execução) e `att532` (`--imax 2`, 1 chance real) — o mínimo para o
mecanismo ter alguma oportunidade de agir, dado o orçamento de tempo desta
sessão. Script da correção:
`scripts/h2_ab_test_fix.py`.

## 5. Metodologia do teste A/B

Comparação pareada (mesma seed, `--pert-mode fixed` em ambos os lados para
isolar o efeito do path relinking sem misturar com o mecanismo de H1):
`./bin/gils_rvnd <instância> --seed N` vs. o mesmo comando + `--path-relinking`.
Script principal: `scripts/h2_ab_test.py`,
correção: `scripts/h2_ab_test_fix.py`. Dados brutos:
`scripts/h2_ab_results.json` e `scripts/h2_ab_results_fix.json`.

| instância | `I_max` usado | seeds | chances reais de PR por execução |
|---|---|---|---|
| eil51 – pr226 | 10 | 15–20 | 9 |
| lin318 | 5 | 10 | 4 |
| pr439 (corrigido) | 3 | 6 | 2 |
| att532 (corrigido) | 2 | 4 | 1 |

## 6. Resultado

| instância | `I_max` | n pares | diff média | win/tie/loss | p (sinal) | overhead de tempo |
|---|---|---|---|---|---|---|
| eil51 | 10 | 20 | 0.000% | 0/20/0 | 1.000 | −0.3% |
| st70 | 10 | 20 | 0.000% | 0/20/0 | 1.000 | −3.4% |
| pr76 | 10 | 20 | 0.000% | 0/20/0 | 1.000 | +3.8% |
| kroA100 | 10 | 15 | 0.000% | 0/15/0 | 1.000 | +1.6% |
| lin105 | 10 | 15 | 0.000% | 0/15/0 | 1.000 | +1.2% |
| pr226 | 10 | 10 | 0.000% | 0/10/0 | 1.000 | −1.3% |
| lin318 | 5 | 10 | **−0.051%** | 2/2/6 | 0.289 | +1.9% |
| pr439 (corrigido) | 3 | 6 | **+0.032%** | 3/2/1 | 0.625 | +14.8% |
| att532 (corrigido) | 2 | 4 | 0.000% | 0/4/0 | 1.000 | +0.1% |

Três achados:

1. **Em toda instância até n=226, base e path-relinking empatam
   exatamente em 100% dos pares** (idêntico ao padrão visto em H1) — essas
   instâncias já são resolvidas de forma tão consistente pelo GILS-RVND
   puro que não há solução alternativa de qualidade equivalente para
   "linkar".
2. **`lin318` (4 chances reais de PR por execução, n=10 seeds)**: leve
   piora média (−0,051%), 2 vitórias / 2 empates / 6 derrotas — não
   significativo (p=0,289), mas direção desfavorável.
3. **`pr439` corrigido (2 chances reais, n=6 seeds)**: leve melhora média
   (+0,032%), 3 vitórias / 2 empates / 1 derrota — não significativo
   (p=0,625), mas direção favorável. Custo de tempo maior que nas outras
   (+14,8%) — plausível, já que com só 3 reinícios o path relinking passa a
   ser uma fração maior do trabalho total.
4. **`att532` corrigido (apenas 1 chance real por execução, n=4 seeds)**:
   empate exato em 100% — amostra fraca demais (só 4 tentativas de PR no
   total) para dizer qualquer coisa.

## 7. Interpretação

`lin318` e `pr439` são os dois únicos pontos onde o mecanismo teve chances
reais suficientes (≥2) para ser avaliado com alguma seriedade — e eles
apontam em **direções opostas**, com magnitudes minúsculas (−0,05% e
+0,03%, ambas dentro do que se esperaria de ruído puro). Isso é o mesmo
padrão de "empate ruidoso em torno de zero" que encontramos na segunda
tentativa de H1 (seção 10.6 do documento de H1) — não uma degradação
sistemática (path relinking não está "quebrando" nada), mas também não uma
melhora confiável.

Isso não invalida o diagnóstico da seção 2 (a diversidade estrutural entre
reinícios realmente cresce com `n`) — só mostra que **a forma específica de
explorar essa diversidade que implementamos** (relink aleatório contra um
membro do pool, uma vez por reinício, guiado só por custo) não a converte em
ganho de qualidade de forma confiável com a quantidade de dados coletada.

## 8. Limitações

- `pr439`/`att532` corrigidos tiveram só 2 e 1 chances reais de path
  relinking por execução, respectivamente (limitado por `I_max` pequeno,
  por sua vez limitado pelo custo de tempo desta sessão) — muito pouco para
  um veredito estatístico; o diagnóstico original (seção 2, `I_max=10`) deu
  ao mecanismo 9 e ~3 chances, um regime bem mais favorável que não foi
  replicado aqui por tempo.
- O guia do path relinking é escolhido **aleatoriamente** entre o pool de
  elite — não necessariamente o membro mais estruturalmente diferente (o
  que a seção 2 sugere ser o ponto onde há mais "coisa nova" a recombinar).
  Escolher o guia por distância de arestas (reaproveitando `edge_distance`,
  já implementado para H1) em vez de aleatoriamente é uma variação não
  testada.
- Path relinking aqui só acontece **entre reinícios externos** (`I_max`),
  nunca dentro do laço ILS interno — a literatura (AILS-PR, ver seção 9 do
  documento de H1) tipicamente também mantém um pool atualizado com mais
  frequência.
- Amostra pequena em toda instância grande (n=4 a 10 pares) — os `p` do
  teste de sinal (0,29 e 0,63) não permitem rejeitar "sem efeito" em nenhum
  dos dois sentidos.

## 9. Recomendação

**Não há evidência suficiente, dos dados coletados, para adotar ou
descartar path relinking.** Diferente de H1 (onde a primeira tentativa foi
claramente refutada por perder de forma sistemática), aqui o resultado é
genuinamente ambíguo — nem ajuda nem piora de forma detectável, com a
amostra que o orçamento de tempo desta sessão permitiu.

Antes de decidir entre adotar ou abandonar H2, os próximos passos com mais
chance de resolver a ambiguidade, em ordem de custo:

1. Rodar `pr439`/`att532` com `I_max` maior (10, como no diagnóstico
   original) e mais seeds, fora de uma sessão interativa — o mecanismo em
   si é barato (overhead <15% mesmo no pior caso medido), o gargalo é só o
   número de reinícios dentro do tempo disponível.
2. Trocar a escolha aleatória do guia por escolha pelo membro do pool mais
   distante estruturalmente (via `edge_distance`) — testar se "linkar com o
   mais diferente" muda o resultado, já que essa era a lógica original do
   diagnóstico (soluções estruturalmente diferentes e de qualidade
   parecida).
3. Se nada disso destravar um sinal, considerar H2 encerrada nesta forma —
   junto com H1, isso sugeriria que o gargalo real do GILS-RVND não está em
   nenhum dos dois mecanismos de diversificação/intensificação testados, e
   vale reconsiderar a lista de hipóteses desde o início.

## 10. Lote noturno — veredito final com poder estatístico real

Item 1 da recomendação acima foi executado (`scripts/night_batch.py`,
`I_max` maior, mais seeds, fora de sessão interativa). Item 2 (guia por
distância em vez de aleatório) não foi implementado — ver seção 11.

| instância | n | `I_max`/`I_ILS` | diff média | win/tie/loss | p (sinal) |
|---|---|---|---|---|---|
| lin318 | 20 | 10/100 | −0,001% | 8/3/9 | 1,000 |
| pr439 | 15 | 5/100 | +0,042% | 7/2/6 | 1,000 |
| att532 | 10 | 3/100 | +0,072% | 2/3/5 | 0,453 |

Mesmo perfil de H1: nenhum `p` significativo, sinais trocando de direção
entre instâncias, magnitude sempre abaixo de 0,1%. Com N grande o
suficiente, o guia escolhido aleatoriamente do pool de elite **não produz
efeito detectável** — nem ajuda nem piora.

**Veredito final**: H2, como implementada (guia aleatório, uma tentativa de
relink por reinício externo), está encerrada — não adotar. O sintoma
diagnosticado na seção 2 (soluções de qualidade parecida mas estrutura
diferente aparecem à medida que `n` cresce) continua válido, mas
recombiná-las por path relinking com guia aleatório não recupera esse valor
na prática.

## 11. O que não foi testado

A ideia da seção 9 (item 2) — escolher o guia pelo membro do pool
estruturalmente mais distante (via `edge_distance`, já implementado em
`src/gils_rvnd.cpp` para H1) em vez de aleatório — não chegou a ser
implementada nem testada. É a variante mais fiel à lógica original do
diagnóstico (soluções distantes estruturalmente, não quaisquer duas do
pool) e é o candidato mais defensável caso alguém queira retomar H2 no
futuro, em vez de repetir o guia aleatório com mais dados.
