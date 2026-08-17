# H12a — Or-opt estendido a segmentos maiores (4, 5, 6)

Status: **ENCERRADA COM SUCESSO — primeiro ganho real de qualidade
estatisticamente significativo de toda a sessão** (H1-H11 foram todos
nulos em qualidade ou só ganharam em tempo). `extended-oropt` bate o
baseline em `pr439` (p=0,007) e `att532` (p=0,002, 10/10 vitórias), com o
efeito crescendo com `n` (nulo em `lin318`) — mesmo padrão de "vantagem
que só aparece em instâncias grandes" observado na literatura de DBMEA/
GQPSO. Custo: ~26% mais tempo em média.

## 1. Motivação

Depois de esgotar a linha de "escapar melhor do mesmo RVND" (H9 LNS, H10
dynasearch, H11 GLS — todos absorvidos ou com platô), pesquisa sobre
fortalecer a própria vizinhança de busca local em vez de mudar como se
escapa dela. Achados da pesquisa:

- Adaptar Lin-Kernighan ao MLP exigiria um critério de ganho reconstruído
  em cima de T/C/Cr (o critério clássico de LK — "aresta nova mais curta
  que a removida" — está errado para custo cumulativo dependente de
  posição), mas é mecanicamente viável porque os passos de uma cadeia LK
  são sequenciais, não simultâneos como em H10 (não precisa de fronteira
  de Pareto). Engenharia grande demais para um primeiro passo.
- Mesmo no TSP puro, a prática usual não vai além de 3-opt — retorno
  decrescente é esperado, mas nunca tínhamos testado.
- Conferindo `docs/mlp-overview.md`: as 5 vizinhanças do artigo-base
  (swap, 2-opt, reinsertion, or-opt2, or-opt3) cobrem realocação de
  segmentos de tamanho 1-3, mas nada maior, e `Solution::evaluateOrOpt(i,
  j, k)` já aceita qualquer tamanho de segmento — só nunca foi chamada com
  `j-i+1 > 3`.

## 2. Diagnóstico (read-only, antes de implementar)

`bin/diag_oropt_long` (compilado à parte): a partir de ótimos locais do
RVND padrão (5 vizinhanças, sem nenhuma mudança), testar se existe
**algum** movimento de or-opt de comprimento 4, 5, 6, 8 ou 10 que melhore
— sem aplicar nada, só contar.

5 ótimos locais em cada uma de `lin318`/`pr439`/`att532`:

```
lin318.tsp trial=0 ... oropt4=0  oropt5=0  oropt6=0  oropt8=6  oropt10=1
lin318.tsp trial=1 ... oropt4=1  oropt5=0  oropt6=0  oropt8=0  oropt10=8
lin318.tsp trial=2 ... oropt4=13 oropt5=19 oropt6=26 oropt8=19 oropt10=19
lin318.tsp trial=3 ... oropt4=0  oropt5=0  oropt6=0  oropt8=0  oropt10=0
lin318.tsp trial=4 ... oropt4=0  oropt5=0  oropt6=0  oropt8=0  oropt10=0
pr439.tsp  trial=0..4 ... (pelo menos 1 melhorando em todos os 5 trials)
att532.tsp trial=0 ... oropt10=1
att532.tsp trial=1 ... oropt4=2 oropt6=4 oropt8=14 oropt10=2
att532.tsp trial=2 ... (nenhum)
att532.tsp trial=3 ... oropt5=1 oropt10=3
att532.tsp trial=4 ... oropt6=1 oropt8=11 oropt10=13
```

**12 de 15 ótimos locais testados tinham pelo menos um movimento de or-opt
longo (≥4) melhorando** — diferente do quase-zero de H9 (LNS) e H10
(dynasearch), que mostravam oportunidade real mas rara/minúscula. Aqui a
oportunidade é consistente na maioria dos casos, e às vezes grande (26
movimentos simultâneos melhorando num único ótimo local de `lin318`).

## 3. Implementação

Aditiva, segue a convenção do projeto:

- `neighborhood_oropt_generic(Solution&, int segLen)` em
  [`src/neighborhoods.cpp`](../../src/neighborhoods.cpp) — generaliza a
  lógica de shift-de-bloco já usada por `neighborhood_oropt2`/`oropt3`
  (verificada equivalente a elas para `segLen=2,3`, byte a byte).
  `neighborhood_oropt4/5/6` chamam essa genérica.
- `RVND_ExtendedOrOpt` em [`src/rvnd.cpp`](../../src/rvnd.cpp) — mesmo
  laço de `RVND()`, só com `oropt4/5/6` adicionadas à lista de
  vizinhanças (8 no total). `RVND()` original intocado.
- `--rvnd-mode single|multi|extended-oropt` em `gils_rvnd` e
  `local_search` (extensão do flag que já existia para H4).

## 4. Corretude

`RVND_ExtendedOrOpt` nunca pode ser pior que `RVND` (é um superconjunto
estrito de vizinhanças dentro do mesmo laço de ILS) — confirmado:

| instância | single | extended-oropt |
|---|---|---|
| eil51 | 9.429 | 9.429 (empate) |
| kroA100 | 958.170 | 958.013 (melhor) |
| lin318 | 5.670.494 | 5.630.429 (melhor) |

## 5. Calibração de tempo (1 seed, `lin318`, `--imax 5 --iils 50`)

| modo | custo | tempo |
|---|---|---|
| single | 5.590.653 | 28,6s |
| extended-oropt | **5.581.880** | **26,1s** |

Melhor em qualidade **e** mais rápido nesta calibração — diferente de
GRASP-AM/GILS-AM-RVND (só mais rápido) e H8/H11 (só mais rápido, quando
muito, nunca melhor qualidade). Ainda é 1 seed, não é teste estatístico.

## 6. Lote pareado — resultado final

`scripts/night_batch.py` repropositado para esta comparação (`single` vs
`extended-oropt`, pareado por seed, `lin318` N=20 / `pr439` N=15 /
`att532` N=10 — mesma config usada em H1/H2/H6). `--imax`/`--iils` iguais
aos usados nos lotes de H1/H2/H6 para essas instâncias. Análise:
`scripts/night_batch_analysis.py`.

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
lin318       20     0,0027 12/1/7         0,359     11,3
pr439        15     0,3311 13/0/2         0,007     42,9
att532       10     0,3878 10/0/0         0,002     23,3
AGREGADO     45     0,1977 35/1/9         0,000     26,0
```

**Ganho real e estatisticamente significativo em `pr439` (p=0,007, +0,33%)
e `att532` (p=0,002, +0,39%, 10 vitórias em 10 seeds — nenhuma derrota)**.
Em `lin318` o efeito é nulo (p=0,359, +0,003% — ruído), mesmo padrão de
"vantagem que só aparece a partir de certo `n`" que a literatura de
DBMEA/GQPSO já apontava (H8) e que aqui finalmente se confirma dentro
desta sessão. Custo: `extended-oropt` é ~11-43% mais lento (agregado
+26%) — head oropt4/5/6 adiciona 3 vizinhanças extras de custo O(n²) por
varredura ao RVND, sem o overhead catastrófico de H4 (que precisava de
~18x mais varreduras completas); aqui é só um fator constante a mais por
convergência.

## 7. Interpretação e recomendação

Diferente de H1/H2/H4/H6 (mecanismo funciona isolado, mas o RVND absorve
a vantagem no pipeline completo) e de H9/H10/H11 (mecanismo teoricamente
sólido mas oportunidade rara/platô), aqui a vantagem **sobrevive ao
pipeline completo de ILS** — porque não é uma vantagem de entrada ou de
escape, é uma vizinhança genuinamente mais forte que o RVND original não
tinha: `oropt4/5/6` encontram ótimos que a busca de 5 vizinhanças nunca
alcançaria, não importa quantas vezes ela reinicie.

**Recomendado adotar** `--rvnd-mode extended-oropt` como alternativa de
qualidade ao `single` em instâncias `n≳400`, com o trade-off explícito de
~20-40% mais tempo de computação. Não recomendado substituir o default
(mantém-se `single` como padrão, seguindo a convenção da sessão de nunca
sobrescrever o comportamento original) — o ganho de qualidade não é
gratuito, e em `lin318` (n=318) não há vantagem que justifique o custo de
tempo extra.

## 8. `oropt8`/`oropt10` (`--rvnd-mode extended-oropt-wide`) — calibração rápida

Implementado `neighborhood_oropt8`/`oropt10` + `RVND_ExtendedOrOptWide` (10
vizinhanças: as 5 originais + `oropt4/5/6/8/10`), mesma convenção aditiva.
Corretude: nunca pior que `single` (verificado em `eil51`/`kroA100`/
`lin318`; `eil51` inclusive achou 9.319, o valor de referência quase-ótimo
já visto nesta sessão). Calibração de 1 seed:

| instância | single | extended-oropt | extended-oropt-wide |
|---|---|---|---|
| lin318 (imax3/iils20) | 5.670.494 | **5.630.429** | 5.647.282 (pior que oropt simples aqui) |
| att532 (imax2/iils100) | 5.617.672 / 142,1s | 5.605.750 / 179,1s | **5.588.190** / 196,1s |

Sinal misto num único seed cada: em `lin318` o "wide" ficou pior que o
"simples" (4-6), em `att532` ficou melhor que os dois. Plausível: mais
vizinhanças por convergência consome mais do orçamento fixo de `iils`
(menos ciclos de perturbação cabem no mesmo número de iterações), então
"wide" pode perder por orçamento mesmo sendo um superconjunto de
movimentos — não é uma comparação limpa como a de corretude (que roda até
convergência total, sem orçamento fixo). Não hpouve tempo de rodar lote
pareado para `wide` nesta sessão; fica como pergunta em aberto.

## 9. `n=1000` (`rand1000`) — o efeito cresce muito com `n`

Calibração de 1 seed, `--imax 1 --iils 100` (mesma referência de orçamento
usada em H8 para esta instância):

| modo | custo | tempo |
|---|---|---|
| single | 10.595.879 | 315,6s |
| extended-oropt | **10.462.530** | 810,4s |

**-1,26% de ganho de qualidade** — bem maior que os +0,33%/+0,39% vistos em
`pr439`/`att532` (n=439/532), confirmando que o efeito cresce com `n`,
consistente com a hipótese original. Mas o custo de tempo também escalou
de forma não-linear: **+156,8% (2,57x mais lento)**, bem acima do +11-43%
visto em n≤532 — a essa escala, mais vizinhanças O(n²) por convergência
custam desproporcionalmente mais caro.

**Apenas 1 seed — não é teste estatístico.** Um lote pareado de verdade
em `n=1000` (N≥10, mesmo rigor do resto da sessão) custaria ~10×(316+810)s
≈ 3+ horas de tempo de máquina só para essa instância — grande demais para
rodar dentro desta sessão interativa sem check-in explícito. Fica como
trabalho de lote noturno/multi-hora, não confirmado ainda com poder
estatístico.

## 10. Recomendação atualizada e encerramento

O resultado de `n=1000` é o mais empolgante da sessão (maior ganho de
qualidade já visto, a favor da hipótese "efeito cresce com n"), mas ainda
é um único ponto de calibração, e um lote pareado de verdade nessa escala
custaria ~3h de máquina — fora do escopo de uma sessão interativa. Decisão
explícita do usuário: **encerrar H12 aqui**, com o resultado já obtido em
n=318/439/532 (poder estatístico real, seção 6) como o veredito válido.
`n≳1000` e `extended-oropt-wide` ficam como extensões **não confirmadas**
(1 seed cada, sinal promissor mas não testado com rigor) — candidatos
naturais para um lote noturno/multi-hora futuro, não para retomar dentro
de uma sessão interativa sem planejamento prévio.

**Estado final adotado**: `--rvnd-mode extended-oropt` (segmentos 4-6)
recomendado para `n≳400` quando qualidade importa mais que tempo (~26%
mais lento, ganho estatisticamente significativo em `pr439`/`att532`);
`single` continua default. `extended-oropt-wide` implementado e
disponível, mas não recomendado sem mais teste.

## 11. Follow-up: `grasp_am` com `extended-oropt` — não se sustenta

Pergunta natural: `grasp_am` (`src/grasp_am.cpp`) faz **1 única**
convergência de RVND por construção, sem laço de ILS/escape — fraqueza já
diagnosticada em `grasp-am-large-scale.md` (perde ~1-2% do `gils_rvnd`
baseline por falta de intensificação, não pela memória adaptativa em si).
Se essa única convergência usasse `extended-oropt` em vez de `single`,
fecharia parte dessa lacuna sem precisar da reestruturação completa que o
`GILS-AM-RVND` fez?

Implementado aditivamente: `--rvnd-mode single|extended-oropt|extended-oropt-wide`
em `src/grasp_am.cpp` (mesma convenção do `gils_rvnd`, `run_rvnd()`
dispatcher, `single` continua default). Corretude ok (empate em `eil51`,
9319 nos dois modos).

Calibração rápida (5 seeds, `lin318`, `--iter 200`) deu sinal
**animador**: 3W/2L, com vitórias grandes (~1-1,8%) — bem maior que o
+0,33%/+0,39% do `gils_rvnd` puro. Lote pareado completo (N=15-20, mesma
escala de `grasp-am-large-scale.md`: `lin318` iter=800, `pr439` iter=500,
`att532` iter=300, `--parent-mode pool`):

```
instance      n  mean_rel%      w/t/l   sign_p   time+%
lin318       20     0,2453 12/0/8         0,503     13,9
pr439        15     0,4696 9/0/6         0,607      7,6
att532       10     0,1658 5/0/5         1,000     17,3
AGREGADO     45     0,3024 26/0/19        0,371     12,6
```

**Não se sustenta.** Mesmo padrão de H1/H2/H6/H9 (calibração pequena
enganosa): com poder estatístico real, nenhuma instância nem o agregado
chega perto de significância (todo p≥0,37), w/t/l equilibrado demais
(12/8, 9/6, 5/5) — o ganho médio positivo (+0,17% a +0,47%) é ruído, não
efeito real. Diferente do `gils_rvnd` puro (onde o mesmo `extended-oropt`
deu ganho real e significativo), aqui a combinação com a construção
enviesada por memória e a ausência de ILS não preserva a vantagem — mais
uma confirmação de que calibrações de N pequeno (aqui N=5) não substituem
teste com poder estatístico, mesmo quando o sinal inicial parece forte.

**Não adotar** `grasp_am --rvnd-mode extended-oropt`. Encerrado.
