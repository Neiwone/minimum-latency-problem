#!/usr/bin/env python3
"""
Regenerate the result tables of docs/tabelas-resultados.md from the raw
checkpoints, so the numbers in the write-up are never typed by hand.

    python3 scripts/make_result_tables.py > docs/tabelas-resultados.md
"""
import json
from collections import defaultdict
from pathlib import Path

from runner import load_runs
from stats import compare_pairs, pair_runs

PROPOSAL = "gils_am_rvnd_dlb"
BASELINE = "mdm_gils_rvnd"
NO_MEMORY = "gils_rvnd_dlb"

LABEL = {
    "mdm_gils_rvnd":          "MDM publicado",
    "gils_am_rvnd_dlb":       "proposta",
    "mdm_gils_rvnd_dlb":      "MDM + busca local nova",
    "mdm_gils_rvnd_dlb_i100": "MDM + busca local, mineração com folga",
    "gils_rvnd_dlb":          "sem memória",
    "gils_am_rvnd_cand12":    "vencedor anterior (H16)",
    "mdm_gils_rvnd_i300":     "MDM na melhor calibração dele",
}

TSPLIB = ["pr226", "a280", "lin318", "pr439", "att532"]
NODES = {"pr226": 226, "a280": 280, "lin318": 318, "pr439": 439, "att532": 532}


def load(*paths):
    d = {}
    for p in paths:
        if Path(p).exists():
            d.update(load_runs(p))
    return d


def pairs(d, solver, base, only=None):
    """Seed-paired comparison of solver vs base: per instance (only those
    where both ran), and over all pairs together."""
    costs = {i: [(b["cost"], s["cost"]) for b, s in prs]
             for i, prs in pair_runs(d, base, solver, instances=only).items()}
    per = {i: compare_pairs(c) for i, c in costs.items()}
    return per, compare_pairs(c for cs in costs.values() for c in cs)


def pct(x):
    return f"{x:+.3f}".replace("-", "−")


def num(x):
    """Thousands separated by a thin space, without touching the rest of a row."""
    return f"{x:,.0f}".replace(",", "\u2009")


def pfmt(p):
    return "< 1e-6" if p < 1e-6 else f"{p:.4f}"


def mean_costs(d, only=None):
    m = defaultdict(list)
    for k, v in d.items():
        inst, s, seed = k.split("|")
        if only and inst not in only:
            continue
        m[(inst, s)].append(v["cost"])
    return m


def main():
    tsplib = load("results/fixed-time/fixed_time_100s.json", "results/fixed-time/fixed_time_100s_breadth.json")
    n500 = load("results/fixed-time/advisor_n500_100s.json")
    n1000 = load("results/fixed-time/advisor_n1000_100s.json")
    sets = [("TSPLIB n >= 200", tsplib, TSPLIB, 10),
            ("Salehipour n = 500", n500, None, 4),
            ("Salehipour n = 1000", n1000, None, 3)]

    print("# Tabelas de resultados\n")
    print("Gerado por `scripts/make_result_tables.py` a partir dos checkpoints brutos.")
    print("Todos os lotes: 100 s de relógio por execução, execuções sequenciais.\n")
    print("## Como ler as colunas\n")
    print("Cada instância foi resolvida várias vezes, com uma semente aleatória diferente")
    print("por execução (10 nas TSPLIB, 4 em n=500, 3 em n=1000). O algoritmo é")
    print("estocástico, então cada semente devolve uma solução diferente.\n")
    print("| coluna | o que é |")
    print("|---|---|")
    print("| **média** | custo médio das execuções daquela instância -- o que se espera "
          "rodando **uma vez** |")
    print("| **melhor** | menor custo entre elas -- o que se obtém rodando várias e "
          "ficando com a melhor |")
    print("| **dif%** | média, par a par, de (custo − custo da referência) / custo da "
          "referência. Negativo = melhor |")
    print("| **V/E/D** | vitórias / empates / derrotas, comparando **semente a semente** "
          "(semente 1 contra semente 1, e assim por diante) |")
    print("| **p** | teste dos sinais bilateral exato sobre esses pares. Pequeno = "
          "difícil de explicar por acaso |")
    print()
    print("A comparação estatística é sempre pareada por semente, nunca entre médias:")
    print("as duas execuções comparadas partem do mesmo sorteio, o que elimina a")
    print("variação da instância e deixa só a diferença entre os algoritmos.\n")

    # ---- 1. headline
    print("## 1. Proposta vs MDM-GILS-RVND publicado\n")
    print("| conjunto | instâncias | seeds | pares | dif% | V/E/D | p |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for name, d, only, seeds in sets:
        per, c = pairs(d, PROPOSAL, BASELINE, only)
        print(f"| {name} | {len(per)} | {seeds} | {c.n} | **{pct(c.mean_rel)}** "
              f"| {c.wins}/{c.ties}/{c.losses} | {pfmt(c.p)} |")

    # ---- 2. per instance, TSPLIB
    print("\n## 2. TSPLIB, por instância\n")
    print("`melhor conhecido` é o valor hoje registrado em")
    print("`instances/solutions/best_solutions.json` -- em `att532` e `a280` ele foi")
    print("atualizado por este trabalho, então o gap contra ele é conservador.\n")
    best = json.loads(Path("instances/solutions/best_solutions.json").read_text())
    per, _ = pairs(tsplib, PROPOSAL, BASELINE, TSPLIB)
    mc = mean_costs(tsplib, TSPLIB)
    print("| instância | n | melhor conhecido | MDM médio | proposta média "
          "| proposta melhor | dif% | V/E/D | p |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for i in TSPLIB:
        p = per[i]
        b = mc[(i, BASELINE)]
        q = mc[(i, PROPOSAL)]
        bks = int(best[i]["cost"]) if i in best else None
        print(f"| `{i}` | {NODES[i]} | {num(bks) if bks else '-'} "
              f"| {num(sum(b)/len(b))} | {num(sum(q)/len(q))} | {num(min(q))} "
              f"| {pct(p.mean_rel)} | {p.wins}/{p.ties}/{p.losses} "
              f"| {pfmt(p.p)} |")

    # ---- 3. per instance, Salehipour tiers
    for name, d, seeds in [("Salehipour n = 500", n500, 4), ("Salehipour n = 1000", n1000, 3)]:
        print(f"\n## 3. {name}, por instância\n")
        per, c = pairs(d, PROPOSAL, BASELINE)
        mc = mean_costs(d)
        print("| instância | MDM médio | MDM melhor | proposta média | proposta melhor "
              "| dif% | V/E/D |")
        print("|---|---:|---:|---:|---:|---:|---:|")
        for i in sorted(per):
            p = per[i]
            b, q = mc[(i, BASELINE)], mc[(i, PROPOSAL)]
            print(f"| `{i.replace('salehipour_', '')}` | {num(sum(b)/len(b))} | {num(min(b))} "
                  f"| {num(sum(q)/len(q))} | {num(min(q))} "
                  f"| {pct(p.mean_rel)} | {p.wins}/{p.ties}/{p.losses} |")
        print(f"| **agregado** | | | | | **{pct(c.mean_rel)}** "
              f"| **{c.wins}/{c.ties}/{c.losses}** |")

    # ---- 4. controls
    print("\n## 4. Controle: mesma busca local, só muda o mecanismo de memória\n")
    print("Referência de cada linha: o braço **sem mecanismo de memória**.\n")
    print("| conjunto | braço | dif% | V/E/D | p |")
    print("|---|---|---:|---:|---:|")
    for name, d, only, seeds in sets:
        for arm in [PROPOSAL, "mdm_gils_rvnd_dlb", "mdm_gils_rvnd_dlb_i100"]:
            per, c = pairs(d, arm, NO_MEMORY, only)
            if not per:
                continue
            print(f"| {name} | {LABEL[arm]} | {pct(c.mean_rel)} "
                  f"| {c.wins}/{c.ties}/{c.losses} | {pfmt(c.p)} |")

    # ---- 5. absolute costs per arm
    #
    # Averaging absolute costs only means something over the SAME instances, and
    # the older TSPLIB arms did not all run on all five -- so each set is
    # restricted to the arms that cover its full instance list.
    print("\n## 5. Custo médio agregado por braço\n")
    print("Média sobre as instâncias do conjunto. Só entram os braços que rodaram em")
    print("**todas** elas -- médias sobre subconjuntos diferentes não são comparáveis.\n")
    print("| conjunto | braço | custo médio | vs MDM publicado |")
    print("|---|---|---:|---:|")
    for name, d, only, seeds in sets:
        mc = mean_costs(d, only)
        insts = {i for i, _ in mc}
        by = defaultdict(dict)
        for (inst, s), v in mc.items():
            by[s][inst] = sum(v) / len(v)
        full = {s: v for s, v in by.items() if set(v) == insts and s in LABEL}
        base = sum(full[BASELINE].values()) / len(insts)
        for s in sorted(full, key=lambda x: -sum(full[x].values())):
            mean = sum(full[s].values()) / len(insts)
            print(f"| {name} | {LABEL[s]} | {num(mean)} | {pct(100*(mean-base)/base)} |")

    # ---- 6. protocol sanity
    print("\n## 6. Sanidade do protocolo\n")
    print("Mecanismos que só agem na fronteira de reinício precisam de reinícios para")
    print("existir. `minerações` é n/a para os braços que não mineram.\n")
    print("| conjunto | braço | reinícios médios | minerações médias | execuções sem minerar |")
    print("|---|---|---:|---:|---:|")
    for name, d, only, seeds in sets:
        agg = defaultdict(lambda: [0, 0, 0, 0])
        for k, v in d.items():
            inst, s, seed = k.split("|")
            if only and inst not in only:
                continue
            a = agg[s]
            a[0] += v.get("restarts", 0)
            a[1] += max(0, v.get("mining_calls", -1))
            a[2] += 1
            if v.get("mining_calls", -1) == 0:
                a[3] += 1
        for s in sorted(agg):
            if s not in LABEL:
                continue
            r, mcall, n, zero = agg[s]
            mines = "n/a" if "mdm" not in s else f"{mcall/n:.1f}"
            zeros = "n/a" if "mdm" not in s else f"{zero}/{n}"
            print(f"| {name} | {LABEL[s]} | {r/n:.1f} | {mines} | {zeros} |")


if __name__ == "__main__":
    main()
