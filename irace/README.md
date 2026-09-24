# irace — tuning de parâmetros do `gils_am_rvnd`

Configuração pronta para rodar [irace](https://mlopez-ibanez.github.io/irace/)
(Iterated Racing) sobre `bin/gils_am_rvnd`. **Nada aqui foi executado** —
monte o binário e rode em outra máquina.

## Arquivos

- `parameters.txt` — espaço de busca: `--pool` (int, 5-60), `--lambda` (real,
  0.0-1.0), `--parent-mode` (categórico: `pool`/`pair`), `--rvnd-mode`
  (categórico: `single`/`extended-oropt`/`extended-oropt-wide`/`lk-escape`).
  `--imax`/`--iils` ficam fixos nos defaults do binário (10/100) — são
  orçamento, não parâmetros do algoritmo em si.
- `instances-train.txt` + `trainInstancesDir=../instances` (em
  `scenario.txt`) — 6 instâncias de treino: `a280`, `berlin52`, `eil51`,
  `eil101`, `kroA100`, `pr76` (n=51 a 280). **Deliberadamente distintas** das
  10 TSPLIB (`st70`...`att532`) e do benchmark Salehipour usados para
  reportar resultados finais em `docs/hypotheses/` — parâmetros ajustados
  nas mesmas instâncias que você usa pra comparar com a literatura ficariam
  overfitted.
- `target-runner` — script chamado pelo irace por
  configuração×instância×seed; roda `bin/gils_am_rvnd`, extrai `COST` da
  saída e imprime só o número (irace minimiza esse valor).
- `scenario.txt` — liga tudo (orçamento `maxExperiments=2000`,
  `parallel=4` — ajuste pro número de núcleos da máquina que for rodar).

## Comandos

Rodar na outra máquina, a partir da raiz do projeto clonado.

### 1. Instalar R + irace

```bash
Rscript -e 'install.packages("irace", repos="https://cloud.r-project.org")'
```

Se der `'lib' is not writable` / `unable to install packages` (comum sem
`sudo`, tenta instalar no diretório de sistema `/usr/local/lib/R/site-library`):
instale numa biblioteca pessoal em vez disso —

```bash
mkdir -p ~/R/library
echo 'R_LIBS_USER=~/R/library' >> ~/.Renviron
Rscript -e 'install.packages("irace", repos="https://cloud.r-project.org", lib=Sys.getenv("R_LIBS_USER"))'
```

(o `.Renviron` garante que sessões futuras do R já enxergam essa biblioteca
sem precisar do `lib=` explícito de novo.)

Opcional — colocar o wrapper de linha de comando `irace` no PATH (senão usa
`Rscript -e 'irace::irace()'` no lugar de `irace` nos comandos abaixo):

```bash
echo "export PATH=\"$(Rscript -e 'cat(system.file(package="irace", "bin"))'):\$PATH\"" >> ~/.bashrc
source ~/.bashrc
```

### 2. Compilar o binário

```bash
make gils_am_rvnd
```

### 3. Rodar o irace

```bash
cd irace
irace
```

(sem o wrapper no PATH: `cd irace && Rscript -e 'irace::irace()'`)

Lê `scenario.txt` automaticamente (é o nome padrão que o irace procura no
diretório atual). Progresso e resultado final vão pro stdout; o estado
completo fica salvo em `irace.Rdata`. Ajuste antes de rodar se quiser:
`maxExperiments` e `parallel` em `scenario.txt` (ver seção abaixo).

### 4. Retomar uma run interrompida

```bash
cd irace
irace --recovery-file irace.Rdata
```

### 5. Aplicar a configuração vencedora

O irace imprime as configurações "elite" ao final (a melhor primeiro).
Traduza os valores impressos direto nas flags do binário, ex.:

```bash
./bin/gils_am_rvnd instances/lin318.tsp --pool 23 --lambda 0.34 \
    --parent-mode pool --rvnd-mode extended-oropt --seed 1
```

### 6. Validar antes de adotar

O irace só garante que a configuração é boa nas instâncias de *treino*; o
ganho real (se houver) só se confirma comparando contra o default atual
(`--pool 20 --lambda 0.50 --parent-mode pool --rvnd-mode single`, ou já
combinado com `--rvnd-mode extended-oropt` que já é o achado adotado deste
projeto) nas instâncias de *reporte* (10 TSPLIB / benchmark Salehipour),
pareado por seed:

```bash
# default atual (já com o achado extended-oropt adotado neste projeto)
./bin/gils_am_rvnd instances/att532.tsp --rvnd-mode extended-oropt --seed 1

# configuração vencedora do irace
./bin/gils_am_rvnd instances/att532.tsp \
    --pool <valor> --lambda <valor> --parent-mode <valor> --rvnd-mode <valor> \
    --seed 1
```

Repetir pareado (mesma seed nos dois) em várias seeds/instâncias grandes
(`lin318`/`pr439`/`att532`, N≥15-20) antes de considerar confirmado — mesmo
rigor estatístico já usado no projeto, ver memória `feedback-experiment-rigor`.

## Ajustes que podem valer a pena antes de rodar

- `maxExperiments` (`scenario.txt`): 2000 é um chute inicial razoável (regra
  de bolso: ≳200 × nº de parâmetros = ≳800 pra 4 parâmetros). Suba se a
  máquina tiver tempo sobrando.
- `parallel` (`scenario.txt`): hoje em 4 — ajuste pro nº de núcleos reais da
  máquina de destino.
- Travar `--rvnd-mode` em `extended-oropt` (removendo do `parameters.txt` e
  fixando via `--rvnd-mode extended-oropt` dentro do `target-runner`) se o
  objetivo for só afinar `pool`/`lambda`/`parent-mode` em cima do achado já
  validado (`extended-oropt`), em vez de o irace também redescobrir o modo de
  vizinhança do zero.
