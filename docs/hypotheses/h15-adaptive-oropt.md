# H15 — Or-opt com `k_max` adaptativo (`--rvnd-mode adaptive-oropt`)

**Veredito: não concluída.** O mecanismo está implementado e validado funcionalmente,
mas não passou por teste estatístico pareado: só há calibração com 1 seed. O achado
funcional: com `--adapt-grow 0.25 --adapt-shrink 0.12`, a política converge sozinha
para `k_max=6` em `lin318`, partindo de 3 ou de 6, o mesmo valor que o
[H12](h12-extended-oropt.md) fixou à mão. Não adotado.

## Hipótese

O `extended-oropt` do [H12](h12-extended-oropt.md) fixa os comprimentos de or-opt em
2..6 e sorteia entre eles uniformemente. Mas o teto útil muda com a instância e a fase
da busca (um `k_max` fixo varre comprimentos que pararam de produzir e nunca tenta
7..12 quando ainda valeriam), e dentro do teto os comprimentos não são igualmente
produtivos. Aprender o teto e os pesos deveria render mais.

## O que foi testado

Em [`src/rvnd_adaptive.cpp`](../../src/rvnd_adaptive.cpp), `--rvnd-mode adaptive-oropt`
(em `gils_am_rvnd` e `gils_rvnd`):

- **Roleta:** swap, 2-opt e reinserção (or-opt 1) com peso fixo 1,0, mais uma entrada
  por comprimento de or-opt em [2, `kMax`], cada uma com peso aprendido.
- **Crédito:** cada varredura é uma tentativa; a que melhora ganha
  `1 + gainScale × (melhoria relativa)`. Recompensa = crédito/tentativas no período.
- **Adaptação:** a cada `--adapt-period` varreduras (padrão 400, acumuladas entre
  chamadas do RVND, pois o estado vive na execução inteira), os pesos seguem
  `w ← (1-ρ)·w + ρ·recompensa_normalizada` (`--adapt-rho`, padrão 0.30), com piso.
  Depois o teto se move: se a fronteira acerta acima de `--adapt-grow` (padrão 0.10),
  `kMax` cresce 1, até 12, e o novo comprimento entra com peso otimista; se acerta
  abaixo de `--adapt-shrink` (padrão 0.02), `kMax` cai 1, nunca abaixo de 3.
  `--adapt-kstart` (padrão 6) é o teto inicial.

A terminação é a do RVND original, então o resultado continua sendo ótimo local das
vizinhanças habilitadas.

## Resultados

Nada aqui é resultado estatístico; tudo é 1 seed.

Com os limiares padrão (`grow=0.10`), `kMax` satura no teto rígido (12) em `eil51` e
`lin318`, porque a fronteira segue acertando ~10%: a política vira "or-opt até 12 com
seleção ponderada". Com `--adapt-grow 0.25 --adapt-shrink 0.12`, o teto passa a decidir:

| Instância | `--adapt-kstart` | `kMax` final | faixa visitada |
|---|---:|---:|---|
| `lin318` | 6 (default) | **6** | 6..6 |
| `lin318` | 3 | **6** | 3..6 |
| `eil51` | 4 | 7 | 4..10 |
| `rand6` (n=6) | 6 | 3 (piso) | 3..6 |

Em `lin318` (`-v`, `--iils 20`), o hit rate cai com o comprimento (0,42 em L=2 → 0,10
em L=12), mas o ganho médio relativo cresce (0,0147 → 0,0361). Um spot check de custo
na mesma seed (`lin318`, `--iils 20`): `single` 5.594.734 (23,6 s), `extended-oropt`
5.571.913 (20,6 s), `adaptive-oropt` padrão 5.590.970 (26,7 s), `adaptive-oropt` com
`grow=0.25 shrink=0.12` 5.581.227.

## O que o comportamento indica

A política escolhe um teto que depende da instância: 6 em `lin318` (de baixo ou de
cima), mais alto (7) na pequena `eil51`, o piso na minúscula. Segmentos longos acertam
menos mas ganham mais quando acertam, o que explica por que a fronteira continua
"valendo a pena" por hit rate puro e favorece uma recompensa ponderada por ganho (o
papel de `gainScale`). Como a política reencontra o `k_max=6` do H12, ao menos não
destrói esse achado; um ganho, se houver, viria de instâncias onde o teto ótimo não é 6.

## Limitações

- Sem lote pareado: falta comparar `adaptive-oropt` com `extended-oropt` com N≥15–20
  em `n≳300` (`lin318`/`pr439`/`att532`), teste de sinal e checagem de tempo.
- Os limiares (`grow`, `shrink`, `period`, `rho`) não foram calibrados (candidatos ao
  irace, em instâncias de treino separadas das de reporte).
- A maioria das hipóteses do projeto que pareciam boas com 1 seed morreu no lote
  pareado (H6, H13, o follow-up do `grasp_am`).
