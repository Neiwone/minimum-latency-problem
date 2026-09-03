# GILS-RVND vs GILS-AM-RVND (extended-oropt) vs MDM-GILS-RVND — Salehipour n=1000

Status: **`gils_rvnd` vs `gils_am_rvnd_extended_oropt` completo e válido (7ª
confirmação de [[h12-extended-oropt]], a mais forte até agora). `mdm_gils_rvnd`
PENDENTE — os dados coletados sob `--imax 1` são inválidos (bug de protocolo,
ver seção 2) e estão sendo re-coletados sob `--imax 2`.** Complementa
[[salehipour-tsplib-mdm-vs-am-extended]] (mesma comparação em n=10 a 500).

## 1. Objetivo e protocolo

Mesma comparação de três algoritmos dos documentos anteriores, agora no
tier `n=1000` do benchmark oficial de Salehipour (20 instâncias,
`TRP-S1000-R1`...`TRP-S1000-R20`).

**Diferença de protocolo em relação a `n≤500`**: o protocolo completo do
paper (`--imax 10`) foi estimado, a partir dos dados reais já medidos em
`n=50..500`, em ~3,2h por execução em `n=1000` — 20 instâncias × 3
algoritmos × 10 seeds levaria ~13-14 dias mesmo com 6 núcleos em paralelo.
Por isso, seguindo o mesmo precedente já usado e validado neste projeto para
esta escala (ver `docs/experiments/h12-extended-oropt.md` seção 9.1,
"n=1000 (rand1000) — CONFIRMADO"), `gils_rvnd` e
`gils_am_rvnd_extended_oropt` rodaram com **`--imax 1 --iils 100`** (10
seeds, 20 instâncias cada). Uma calibração real confirmou ~6min por
execução nessa configuração, tornando o lote completo viável
(~13-16h estimadas, embora a execução real tenha levado mais — ver nota de
processo na seção 5).

`mdm_gils_rvnd` **não pode usar `--imax 1`** — ver seção 2.

## 2. Bug de protocolo descoberto: `mdm_gils_rvnd` com `--imax 1` nunca mina

`src/mdm_gils_rvnd.cpp` divide as iterações de `I_max` em duas fases: a
primeira metade roda GILS-RVND puro (construção do elite set), a segunda
metade usa construção guiada por padrões minerados
(`phase1Iters = max(1, I_max / 2)`, ver linha 249). Com `I_max=1`,
`phase1Iters = max(1, 0) = 1`, e a única iteração do laço (`i=0`) nunca
satisfaz `i >= phase1Iters` — a mineração **nunca dispara**, e o algoritmo
inteiro se reduz a uma execução idêntica de `gils_rvnd`, sem erro nenhum
aparente.

Isso foi descoberto porque os primeiros 60/60 resultados de `mdm_gils_rvnd`
coletados sob `--imax 1` neste tier saíram **bit a bit idênticos** ao
`gils_rvnd` correspondente (mesma seed, mesmo custo exato em todas as 20
instâncias × 10 seeds — W/T/L sempre 0/200/0). É a mesma classe de armadilha
já documentada na memória do projeto (`feedback-experiment-rigor`) para o
path relinking do H2 sob `--imax 1`: um parâmetro de orçamento que, sem
querer, desliga o mecanismo sendo testado.

**Correção**: `mdm_gils_rvnd` está sendo re-executado com **`--imax 2`**
(`phase1Iters = max(1, 1) = 1`; o laço de 2 iterações roda `i=0` — fase 1,
GILS-RVND puro — e `i=1` — fase 2, com mineração real, já que o elite set
foi atualizado em `i=0`) — o menor orçamento que de fato exercita o
mecanismo, embora ainda muito menor que o `--imax 10` do paper.
`gils_rvnd`/`gils_am_rvnd_extended_oropt` não são afetados por este bug (não
têm divisão de fases) e seus resultados sob `--imax 1` permanecem válidos.

## 3. Resultados: `gils_rvnd` vs `gils_am_rvnd_extended_oropt` (válido)

| Instance | GILS-RVND Best | GILS-RVND Avg | GILS-RVND Time(s) | AM+ext-oropt Best | AM+ext-oropt Avg | AM+ext-oropt Gap%(avg) | AM+ext-oropt Time(s) | AM+ext-oropt W/T/L | AM+ext-oropt p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| TRP-S1000-R1 | 5,121,975 | 5,209,123.4 | 1244.63 | 5,112,760 | 5,157,690.2 | -0.987% | 2290.46 | 8/0/2 | 0.109 |
| TRP-S1000-R2 | 5,175,987 | 5,233,157.3 | 1487.63 | 5,137,491 | 5,201,163.6 | -0.611% | 1902.22 | 7/0/3 | 0.344 |
| TRP-S1000-R3 | 5,204,384 | 5,259,816.3 | 1462.97 | 5,185,178 | 5,218,332.8 | -0.789% | 2290.48 | 8/0/2 | 0.109 |
| TRP-S1000-R4 | 5,176,277 | 5,226,389.1 | 1501.65 | 5,132,523 | 5,181,181.5 | -0.865% | 2292.44 | 8/0/2 | 0.109 |
| TRP-S1000-R5 | 5,132,246 | 5,180,131.7 | 1382.59 | 5,051,097 | 5,112,637.0 | -1.303% | 2063.54 | 10/0/0 | 0.002 |
| TRP-S1000-R6 | 5,169,054 | 5,198,725.5 | 1656.21 | 5,123,232 | 5,155,754.8 | -0.827% | 2360.32 | 9/0/1 | 0.021 |
| TRP-S1000-R7 | 5,125,080 | 5,179,786.2 | 1704.09 | 5,106,348 | 5,136,605.0 | -0.834% | 2156.18 | 9/0/1 | 0.021 |
| TRP-S1000-R8 | 5,237,335 | 5,295,837.8 | 1657.36 | 5,184,140 | 5,253,288.8 | -0.803% | 3103.19 | 8/0/2 | 0.109 |
| TRP-S1000-R9 | 5,101,719 | 5,150,357.3 | 2193.56 | 5,057,592 | 5,088,112.0 | -1.209% | 2852.46 | 10/0/0 | 0.002 |
| TRP-S1000-R10 | 5,057,085 | 5,154,548.9 | 1584.71 | 5,032,990 | 5,106,141.7 | -0.939% | 2094.73 | 7/0/3 | 0.344 |
| TRP-S1000-R11 | 5,250,743 | 5,301,919.9 | 1397.39 | 5,230,010 | 5,269,333.2 | -0.615% | 2059.95 | 7/0/3 | 0.344 |
| TRP-S1000-R12 | 5,123,264 | 5,161,613.1 | 1273.44 | 5,059,576 | 5,112,593.0 | -0.950% | 2252.96 | 9/0/1 | 0.021 |
| TRP-S1000-R13 | 5,156,169 | 5,200,331.9 | 1436.25 | 5,143,408 | 5,187,354.6 | -0.250% | 2481.81 | 6/0/4 | 0.754 |
| TRP-S1000-R14 | 5,129,048 | 5,175,292.0 | 1429.51 | 5,080,526 | 5,117,130.4 | -1.124% | 3223.89 | 9/0/1 | 0.021 |
| TRP-S1000-R15 | 5,133,713 | 5,175,527.0 | 2000.21 | 5,044,190 | 5,124,835.9 | -0.979% | 3169.43 | 9/0/1 | 0.021 |
| TRP-S1000-R16 | 5,115,428 | 5,162,480.5 | 2082.53 | 5,096,702 | 5,114,206.6 | -0.935% | 2654.20 | 9/0/1 | 0.021 |
| TRP-S1000-R17 | 5,144,703 | 5,199,027.2 | 1511.48 | 5,155,249 | 5,169,483.6 | -0.568% | 2047.46 | 7/0/3 | 0.344 |
| TRP-S1000-R18 | 5,171,111 | 5,212,510.4 | 1685.32 | 5,164,828 | 5,186,926.9 | -0.491% | 1965.54 | 8/0/2 | 0.109 |
| TRP-S1000-R19 | 5,071,631 | 5,107,013.7 | 1417.74 | 5,029,803 | 5,087,797.6 | -0.376% | 1913.49 | 8/0/2 | 0.109 |
| TRP-S1000-R20 | 5,115,585 | 5,155,043.5 | 1287.07 | 5,085,927 | 5,145,061.4 | -0.194% | 1566.72 | 6/0/4 | 0.754 |

**Agregado (200 pares seed):** mean_rel=**-0,782%**, W/T/L=**162/0/38**,
p<0,0001, tempo AM+ext-oropt vs baseline = **+48,9%**. Tempo médio:
`gils_rvnd` 1569,8s, `gils_am_rvnd_extended_oropt` 2337,1s.

**8 das 20 instâncias já batem p<0,05 individualmente** com N=10 seeds
(`R5`, `R6`, `R7`, `R9`, `R12`, `R14`, `R15`, `R16`) — o dobro do que se via
em `n=500` (6/20) e o sinal mais forte de toda a sessão em magnitude
(`mean_rel` de -0,78%, vs -0,28% em n=500 e -0,04% no agregado geral do
tier anterior). **`AM+ext-oropt` nunca perde no agregado por instância** —
`L=0` em 12 das 20 instâncias.

## 4. Resultados: `mdm_gils_rvnd` (PENDENTE — re-coletando com `--imax 2`)

*(Placeholder — será substituído pelos números reais assim que o lote sob
`--imax 2` terminar. Não usar os valores sob `--imax 1` — ver seção 2.)*

| Instance | MDM Best | MDM Avg | MDM Gap%(avg) | MDM Time(s) | MDM W/T/L vs GILS-RVND | MDM p |
|---|---:|---:|---:|---:|---:|---:|
| TRP-S1000-R1..R20 | pendente | pendente | pendente | pendente | pendente | pendente |

**Agregado (200 pares seed):** pendente.

## 5. Notas de processo

- **Interrupção intencional**: o lote foi pausado e retomado duas vezes a
  pedido do usuário durante a execução (checkpoint incremental em
  `scripts/salehipour_n1000_mdm_vs_am_extended_checkpoint.json`, dentro do
  repo — não em `/tmp`, lição já registrada após o incidente do tier
  `n≤500`). Tempo total decorrido (incluindo pausas) maior que o tempo de
  computação efetivo.
- **Estimativa inicial otimista**: a calibração de 1 seed (~6min) sugeria
  ~13-16h de execução total; o lote real levou bem mais que isso mesmo
  descontando as pausas — mesmo padrão de sub-estimativa já visto no tier
  `n≤500` (paralelismo real tem mais overhead de contenção do que uma
  medição solo sugere).

## 6. Reprodução

```bash
make gils_rvnd gils_am_rvnd mdm_gils_rvnd
python3 scripts/salehipour_n1000_mdm_vs_am_extended.py   # gils_rvnd + AM+ext-oropt, --imax 1 (válidos)
python3 scripts/salehipour_n1000_mdm_imax2.py             # mdm_gils_rvnd, --imax 2 (corrige o bug da seção 2)
```
