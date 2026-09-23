# Como rodar o lote na outra máquina

Dois lotes de tempo fixo sobre o benchmark Salehipour, que produzem os números do
documento para o orientador. **~20 h de máquina no total**, retomável.

## 1. Pré-requisitos

- `g++` com C++17 e `make`
- `python3` (só biblioteca padrão — o runner não precisa de `uv` nem de pacote nenhum)
- As 140 instâncias já estão versionadas em `instances/salehipour/`; não precisa gerar nada.

## 2. Rodar

```bash
git clone <repo> && cd minimum-latency-problem
git checkout <branch>

nohup setsid bash scripts/run_advisor_batches.sh > scripts/advisor_run.log 2>&1 &
```

O `setsid` é o que faz o lote sobreviver a uma queda de SSH. O script começa
compilando e rodando um *preflight* (cada braço roda 5 s e tem o tour conferido contra
as coordenadas) — se algo estiver quebrado, ele para ali em vez de descobrir depois de
oito horas.

## 3. Acompanhar

```bash
tail -f scripts/advisor_run.log          # linha por execução concluída
grep -c "^\[" scripts/advisor_run.log    # quantas já terminaram (de 700)
```

Cada linha traz custo, tempo e número de reinícios, e marca com `[!]` as execuções em
que um mecanismo de fronteira de reinício não disparou.

## 4. Se parar no meio

Reboot, Ctrl-C, queda de energia: **rode o mesmo comando de novo**. Os checkpoints
ficam em `scripts/advisor_n1000_100s.json` e `scripts/advisor_n500_100s.json`, e o
script pula tudo que já foi feito.

## 5. Três regras que anulam o resultado se quebradas

1. **Nada pesado rodando junto.** Comparação de tempo não sobrevive a disputa por CPU:
   medido neste projeto, 3 processos concorrentes custam 27% da vazão. Compilar, abrir
   o navegador, rodar outro experimento — tudo isso contamina.
2. **Uma cópia só.** Não inicie o script duas vezes; as execuções têm que ser
   sequenciais.
3. **Não misture máquinas.** Todos os braços de uma comparação têm que vir da mesma
   máquina. Os lotes anteriores (`scripts/fixed_time_100s*.json`) são de outra máquina
   e não podem ser comparados com estes — estes são autocontidos justamente por isso.

> **Cuidado com um detalhe do runner.** `--mode fixed-time` sem `--checkpoint`
> **apaga** o checkpoint default daquele orçamento (`scripts/fixed_time_<T>s.json`)
> antes de começar. O script deste lote sempre passa `--checkpoint`, então está
> seguro — mas não rode um `run_experiments.py --mode fixed-time` solto na mesma
> máquina enquanto o lote roda.

## 6. O que mandar de volta

```
scripts/advisor_n1000_100s.json
scripts/advisor_n500_100s.json
scripts/advisor_run.log
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

O n=1000 vem primeiro de propósito: é a escala que falta e a primeira pergunta
provável do orientador. Se só der para rodar um, rode esse.
