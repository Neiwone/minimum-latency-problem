# Tuning automático (irace) do método proposto

**Resumo.** O irace ajustou os quatro parâmetros da busca local do `gils_am_rvnd_dlb`
no protocolo de tempo fixo (100 s), partindo da configuração atual. Ele convergiu para
uma região **vizinha** dela: K = 13–14, maxlen = 6–7, or-opt invertido ligado,
`I_ILS` entre 289 e 499. Validada em 6 instâncias que o irace não viu, a melhor
configuração dele **empata** com a atual:

| | `cand-k` | `cand-maxlen` | or-opt invertido | `I_ILS` |
|---|---:|---:|---|---:|
| atual (`gils_am_rvnd_dlb`) | 12 | 6 | ligado | 300 |
| irace (config 82) | 14 | 7 | ligado | 396 |

Config 82 contra a atual: **+0,100%** (pior), 24/0/36 em 60 pares, p = 0,155.

A configuração atual fica, agora com uma justificativa formal: o tuning automático
não encontra nada melhor do que ela.

---

## 1. Desenho

### 1.1 Espaço de parâmetros

São os parâmetros da busca local que a
[ablação](../reports/ablation-gils-rvnd-to-dlb.md) mostrou importar
([`irace/parameters-dlb.txt`](../../irace/parameters-dlb.txt)):

| parâmetro | domínio | atual |
|---|---|---:|
| `--cand-k` (tamanho da lista de candidatos) | inteiro, 6 a 30 | 12 |
| `--cand-maxlen` (maior bloco de or-opt) | inteiro, 3 a 8 | 6 |
| or-opt invertido | ligado / desligado | ligado |
| `--iils` | inteiro, 50 a 1 000, escala log | 300 |

λ e `pool`, da memória adaptativa, ficaram nos valores padrão: a ablação mostrou que a
memória não tem efeito, e incluí-los gastaria orçamento sem retorno. O `--rvnd-mode`
fica fixo em `candidate-dlb`.

### 1.2 Instâncias

- **Treino** (o irace só vê estas): 8 TSPLIB `EUC_2D` com n ≥ 500: `u574`, `rat575`,
  `p654`, `d657`, `u724`, `u1060`, `vm1084`, `rl1304`.
- **Teste** (só a validação vê estas): as 6 da ablação: `att532`, `rat783`, `pr1002`,
  `pcb1173`, `d1291`, `nrw1379`.

Os conjuntos são disjuntos, para a validação medir o que a configuração escolhida vale
em instâncias novas, não o quanto ela se ajustou às de treino. O critério n ≥ 500 é o
mesmo da ablação: abaixo disso o método satura em 100 s.

### 1.3 Orçamento

- 600 experimentos de 100 s cada, 3 em paralelo (~5,8 h de relógio). A disputa por CPU
  entre 3 processos custa ~27% da vazão
  ([protocolo](fixed-time-protocol.md)), igual para todas as configurações de uma
  corrida.
- A configuração atual entra como configuração inicial
  ([`configurations-dlb.txt`](../../irace/configurations-dlb.txt)): o irace tem de
  superá-la para mudar alguma coisa.

## 2. O que o irace fez

82 configurações avaliadas em 5 iterações:

| iteração | elites (da melhor para a pior) |
|---|---|
| 1 | **1 (atual)**, 20, 16, 24 |
| 2 | 40, 20, 16, **1 (atual)** |
| 3 | 55, 16, 20, 40 |
| 4 | 82, 55, 67, 80 |
| 5 (final) | **82**, 55, 67, 80 |

| config | `cand-k` | `cand-maxlen` | invertido | `I_ILS` |
|---|---:|---:|---|---:|
| 82 | 14 | 7 | ligado | 396 |
| 55 | 13 | 6 | ligado | 365 |
| 67 | 13 | 6 | ligado | 499 |
| 80 | 13 | 6 | ligado | 289 |

Três observações:

- **A região vencedora cerca a configuração atual.** As quatro elites finais têm K de
  13 a 14 (atual: 12), maxlen de 6 a 7 (atual: 6) e `I_ILS` de 289 a 499 (atual: 300).
- **O or-opt invertido sobreviveu.** Configurações sem ele foram testadas (31 de 82) e
  nenhuma chegou às elites finais. Isso confirma, por outro caminho, que as vizinhanças
  extras pagam a 100 s ([ablação](../reports/ablation-gils-rvnd-to-dlb.md), seção 3).
- **Os extremos foram descartados.** K alto (até 30), blocos curtos (maxlen 3–4) e
  `I_ILS` muito baixo ou muito alto foram testados e eliminados pela corrida, o que
  reproduz as triagens do [H19](../hypotheses/h19-dlb-fast-regime.md) (K = 20 e 30
  piores; maxlen 3 e 4 piores; `I_ILS` 1 000 e 3 000 piores).

A configuração atual saiu das elites na iteração 3, depois de 9 execuções. Nas 9
rodadas de treino em que ela e a config 82 foram medidas lado a lado, a 82 ganhou 6,
empatou 1 e perdeu 2 (−0,12% em média). É pouco para concluir algo, e é exatamente o
tipo de vantagem que se espera por acaso de um vencedor escolhido entre 82
candidatos.

## 3. Validação

A config 82 contra a atual, nas 6 instâncias de teste, no protocolo oficial: 100 s,
sequencial, seeds 1–10 pareadas (60 pares). Positivo = a config 82 é pior.

| instância | rel% | V/E/D | p (sinais) | custo médio atual | custo médio irace |
|---|---:|---:|---:|---:|---:|
| `att532` | +0,063 | 5/0/5 | 1,000 | 5 587 356,4 | 5 590 892,0 |
| `rat783` | +0,535 | 1/0/9 | 0,022 | 3 195 093,0 | 3 212 144,3 |
| `pr1002` | +0,012 | 4/0/6 | 0,754 | 116 382 623,6 | 116 393 632,0 |
| `pcb1173` | +0,393 | 2/0/8 | 0,109 | 31 098 150,8 | 31 219 729,2 |
| `d1291` | +0,164 | 5/0/5 | 1,000 | 29 492 750,4 | 29 540 782,6 |
| `nrw1379` | −0,570 | 7/0/3 | 0,344 | 35 740 619,9 | 35 536 095,4 |
| **agregado** | **+0,100** | **24/0/36** | **0,155** | | |

**Empate.** O agregado não é significativo e as instâncias apontam para os dois lados:
a config 82 vai melhor em `nrw1379` (−0,57%) e pior em `rat783` (+0,54%, a única
instância com p < 0,05, que não sobreviveria a uma correção para 6 comparações). Se há
alguma tendência, é contra a configuração do irace.

Os dois braços completaram em média 2,1 e 1,8 reinícios por execução: com `I_ILS` alto
e n ≥ 500, quase todo o orçamento vai para uma única trajetória de ILS, como nas
execuções da ablação.

## 4. Conclusão

1. **A configuração atual (K = 12, maxlen = 6, invertido ligado, `I_ILS` = 300) fica.**
   O irace, partindo dela e explorando 82 configurações, não encontrou nada que a
   supere em instâncias novas.
2. **A superfície de parâmetros é plana perto do ótimo.** Variações de ±2 em K, ±1 em
   maxlen e ±100 em `I_ILS` não mudam o resultado de forma mensurável. Para o método,
   isso é uma boa notícia: ele não depende de um ajuste fino.
3. **Os componentes do método são confirmados pelo tuning.** O irace tinha liberdade
   para desligar o or-opt invertido, usar listas grandes ou blocos curtos, e não fez
   nenhuma dessas coisas.

## 5. Limitações

1. **Orçamento modesto.** 600 experimentos para 4 parâmetros fica no limite inferior
   do que se recomenda para o irace. Uma região melhor, distante da atual, poderia ter
   escapado, embora as 82 configurações tenham coberto os domínios inteiros (K de 6 a
   30, `I_ILS` de 57 a 949).
2. **Treino com 3 processos concorrentes.** As execuções do irace receberam o
   equivalente a ~73 s sequenciais, não 100 s. A validação, sequencial, corrige isso
   para a comparação final, mas o irace escolheu parâmetros para um orçamento um pouco
   menor.
3. **Ruído alto por execução.** Com 1–2 reinícios por execução, o custo final varia
   bastante entre seeds, o que dificulta para o irace separar configurações próximas.
4. **Só o orçamento de 100 s.** Com outro orçamento, o `I_ILS` ótimo provavelmente muda.

## 6. Onde está cada coisa

| o quê | onde |
|---|---|
| cenário, espaço, instâncias e runner | [`irace/`](../../irace/), arquivos `*-dlb*` ([README](../../irace/README.md)) |
| estado completo do irace | `irace/irace-dlb.Rdata`; log em `irace/irace-dlb.log` |
| configuração do irace no registro de solvers | `gils_am_rvnd_irace` em [`scripts/registry.py`](../../scripts/registry.py) |
| dados da validação (120 execuções) | [`results/fixed-time/irace_validation_100s.json`](../../results/fixed-time/irace_validation_100s.json) |
