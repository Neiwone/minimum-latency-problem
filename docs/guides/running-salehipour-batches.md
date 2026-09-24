# Como rodar os lotes Salehipour n=500 e n=1000

Dois lotes de tempo fixo sobre o benchmark Salehipour, que produzem os números de
n=500 e n=1000 em [results-tables](../results-tables.md). **~20 h de máquina no total**, retomável.

## 1. Pré-requisitos

- `g++` com C++17 e `make`
- `python3` (só biblioteca padrão — o runner não precisa de `uv` nem de pacote nenhum)
- As 140 instâncias já estão versionadas em `instances/salehipour/`; não precisa gerar nada.

## 2. Rodar

```bash
git clone <repo> && cd minimum-latency-problem
git checkout <branch>

mkdir -p logs && nohup setsid bash scripts/run_advisor_batches.sh > logs/advisor_run.log 2>&1 &
```

O `setsid` é o que faz o lote sobreviver a uma queda de SSH. O script começa
compilando e rodando um *preflight* (cada braço roda 5 s e tem o tour conferido contra
as coordenadas) — se algo estiver quebrado, ele para ali em vez de descobrir depois de
oito horas.

## 3. Acompanhar

```bash
tail -f logs/advisor_run.log          # linha por execução concluída
grep -c "^\[" logs/advisor_run.log    # quantas já terminaram (de 700)
```

Cada linha traz custo, tempo e número de reinícios, e marca com `[!]` as execuções em
que um mecanismo de fronteira de reinício não disparou.

## 4. Se parar no meio

Reboot, Ctrl-C, queda de energia: **rode o mesmo comando de novo**. Os checkpoints
ficam em `results/fixed-time/advisor_n1000_100s.json` e `results/fixed-time/advisor_n500_100s.json`, e o
script pula tudo que já foi feito.

## 5. Três regras que anulam o resultado se quebradas

1. **Nada pesado rodando junto.** Comparação de tempo não sobrevive a disputa por CPU:
   medido neste projeto, 3 processos concorrentes custam 27% da vazão. Compilar, abrir
   o navegador, rodar outro experimento — tudo isso contamina.
2. **Uma cópia só.** Não inicie o script duas vezes; as execuções têm que ser
   sequenciais.
3. **Não misture máquinas.** Todos os braços de uma comparação têm que vir da mesma
   máquina. Os lotes anteriores (`results/fixed-time/fixed_time_100s*.json`) são de outra máquina
   e não podem ser comparados com estes — estes são autocontidos justamente por isso.

> **Checkpoints antigos não são retomáveis.** O `run_experiments.py` agora grava a
> configuração do lote no checkpoint e se recusa a retomar um arquivo sem ela. Os
> dois checkpoints deste lote são anteriores a isso: o lote já terminou, mas rodar
> este script de novo em cima deles dá erro. Para um lote novo, aponte
> `--checkpoint` para arquivos novos.

## 6. O que mandar de volta

```
results/fixed-time/advisor_n1000_100s.json
results/fixed-time/advisor_n500_100s.json
logs/advisor_run.log
```

Os dois `.json` são os dados; o `.log` serve para auditar tempos e mecanismos.

## 7. O que os lotes respondem

Cinco braços nos mesmos runs, para que a manchete e os controles saiam dos mesmos dados:

| braço | pergunta que responde |
|---|---|
| `mdm_gils_rvnd` | a manchete: quanto a proposta ganha do estado da arte publicado |
| `gils_am_rvnd_dlb` | ↑ (a proposta) |
| `mdm_gils_rvnd_dlb` | o ganho é da busca local ou da estratégia? |
| `mdm_gils_rvnd_dlb_i100` | idem, com a mineração do MDM rodando com folga |
| `gils_rvnd_dlb` | algum mecanismo de memória vale alguma coisa? |

| lote | instâncias | seeds | execuções | tempo |
|---|---:|---:|---:|---:|
| Salehipour n=1000 | 20 | 3 | 300 | ~8,5 h |
| Salehipour n=500 | 20 | 4 | 400 | ~11,5 h |

O n=1000 vem primeiro de propósito: é a escala que ainda não tinha sido medida. Se só der para rodar um, rode esse.
