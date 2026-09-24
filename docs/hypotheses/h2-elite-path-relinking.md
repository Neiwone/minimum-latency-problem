# H2 — Path relinking entre elites

> Os scripts e dados brutos em `scripts/` citados neste documento foram removidos do
> repositório e estão preservados na tag git `archive/h-scripts`
> (`git show archive/h-scripts:scripts/<arquivo>`).

**Veredito: refutada, na forma implementada.** O sintoma existe, mas é distinto do
enunciado: os reinícios não descartam soluções muito melhores, e sim soluções de
qualidade equivalente e estrutura diferente. Path relinking com guia aleatório não
converte isso em ganho: com poder estatístico (N=20/15/10 em
`lin318`/`pr439`/`att532`) o efeito é indistinguível de ruído (p ≥ 0,30 em todas,
magnitude média sempre < 0,1%). Não adotado.

## Hipótese

O GILS-RVND guarda só o melhor global entre as `I_max` reinicializações. Se soluções
boas aparecem em reinícios diferentes e são descartadas, manter um pool elite e
explorar os caminhos entre elas (path relinking) recuperaria qualidade que o ILS puro
perde.

## Diagnóstico do sintoma

Com o trace `-v` de `gils_rvnd` (ver [H1](h1-adaptive-diversification.md)) e os
parâmetros do artigo (`--imax 10 --iils 100`), extraiu-se a solução final de cada
reinício externo. `spread%` = diferença entre pior e melhor; `mean_jacc` = Jaccard
médio das arestas dirigidas entre a melhor e as demais.

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

Os reinícios convergem para custo muito parecido (spread ≤ 2,3%), então o descarte
quase nunca joga fora uma solução muito pior. Mas a similaridade estrutural cai nas
duas maiores instâncias (`lin318`: 0.438, `pr439`: 0.316, contra 0.7–1.0 nas menores):
soluções de qualidade quase idêntica compartilham menos da metade dos arcos. É o
cenário clássico em que path relinking tende a compensar, embora a tendência se apoie
em só 2 pontos (o segundo com poucos reinícios válidos).

## O que foi testado

Em [`src/gils_rvnd.cpp`](../../src/gils_rvnd.cpp), ativado por `--path-relinking`
(padrão desligado; sem a flag o comportamento é idêntico ao artigo):

- Pool elite de até `--elite-size` soluções (padrão 5), só tour + custo, deduplicado
  por igualdade exata de rota, descartando a pior quando cheio.
- Path relinking clássico por troca posicional (Glover): percorre as posições da
  solução de partida; onde ela difere do guia, troca o elemento atual pelo que o guia
  pede, recalcula o custo e guarda o melhor ponto do caminho. É `O(n³)` por chamada,
  mas roda uma vez por reinício externo, não no laço ILS (overhead <1% em `lin318`).
- Ao fim de cada reinício, escolhe **um membro aleatório do pool** como guia, faz o
  relink a partir da solução do reinício, aplica RVND no melhor ponto do caminho e
  substitui a solução se melhorar; depois adiciona a solução do reinício ao pool.

Comparação pareada: mesma seed, `--pert-mode fixed` nos dois lados (para não misturar
com H1), com e sem `--path-relinking`.

## Resultados

**Primeira rodada** (N=4 a 20): até `n=226` (`I_max=10`) base e path relinking empatam
em 100% dos pares; `lin318` (`I_max=5`) ficou em −0.051%, 2/2/6, p=0.289; `pr439`
(`I_max=3`) em +0.032%, 3/2/1, p=0.625; `att532` (`I_max=2`) empate exato em 4 pares.
Uma primeira versão usou `--imax 1` em `pr439`/`att532`, o que invalidava o teste: o
pool só recebe o primeiro membro quando o único reinício termina, então o path
relinking nunca executava.

**Lote final, com poder estatístico** (diferença positiva = path relinking melhor):

| instância | n | `I_max`/`I_ILS` | diff média | win/tie/loss | p (sinal) |
|---|---|---|---|---|---|
| lin318 | 20 | 10/100 | −0,001% | 8/3/9 | 1,000 |
| pr439 | 15 | 5/100 | +0,042% | 7/2/6 | 1,000 |
| att532 | 10 | 3/100 | +0,072% | 2/3/5 | 0,453 |

Mesmo perfil de H1: nenhum `p` significativo, sinal trocando entre instâncias,
magnitude sempre abaixo de 0,1%.

## Por que não funcionou

- Até `n=226` o GILS-RVND puro já resolve as instâncias de forma tão consistente que
  não há solução alternativa de qualidade equivalente para "linkar".
- Nas maiores, o path relinking não degrada nada de forma sistemática, mas também não
  melhora: o diagnóstico (diversidade estrutural crescendo com `n`) continua válido,
  só que relink contra um membro aleatório do pool, uma vez por reinício e guiado só
  por custo, não recupera esse valor.

Não testado: escolher como guia o membro do pool **estruturalmente mais distante**
(via a distância de arestas já implementada para H1) em vez de um aleatório. É a
variante mais fiel à lógica do diagnóstico e o candidato mais defensável para retomar
H2.

## Limitações

- Relink só entre reinícios externos, nunca dentro do laço ILS; a literatura (AILS-PR,
  ver [H1](h1-adaptive-diversification.md)) atualiza o pool com mais frequência.
- Em `pr439` e `att532` o lote usou `I_max` reduzido (5 e 3) por custo de tempo, o que
  limita as chances de relink por execução.
- Na primeira rodada o `pr439` teve overhead de tempo de +14,8% (com só 3 reinícios o
  relink pesa mais); nas demais instâncias ficou entre −3,4% e +3,8%.
