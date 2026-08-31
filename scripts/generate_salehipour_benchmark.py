"""
Gera o conjunto de instancias seguindo o protocolo documentado de
Salehipour, Sorensen, Goos & Braysy -- "Efficient GRASP+VND and
GRASP+VNS metaheuristics for the traveling repairman problem", 4OR
9:189-209 (2011), Secao 4 -- usado no paper-base (Silva et al. 2012,
GILS-RVND) e em DBMEA/GQPSO/MDM-GILS-RVND para avaliar em instancias
grandes: 7 tamanhos (10, 20, 50, 100, 200, 500, 1000), 20 instancias
aleatorias por tamanho (coordenadas uniformes), 140 instancias no total.

Protocolo exato (Secao 4 do paper, Table 1): coordenadas uniformes em
[0,100] para n in {10,20,50,100,200}, em [0,500] para n in {500,1000};
distancias euclidianas arredondadas PARA BAIXO (floor) ao inteiro mais
proximo -- ja e' exatamente o que src/evaluator.cpp faz para EUC_2D
((int)(d), trunca positivos = floor), entao nao precisa de nenhuma
mudanca no motor C++, so o grid de geracao por tamanho precisa bater.

Os arquivos originais dos autores nao estao publicamente disponiveis
("available from the authors upon request", pagina 199) -- este script
reproduz o protocolo documentado usando o gerador ja existente do
projeto (scripts/instance_generator.py).

Salvas em instances/salehipour/, nomeadas
salehipour_n{tamanho:04d}_i{indice:02d}.tsp (indice 1..20).

Uso: uv run scripts/generate_salehipour_benchmark.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from instance_generator import generate_dmp_instance, save_as_tsplib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "instances" / "salehipour"

N_PER_SIZE = 20

# (tamanho, grid) -- Table 1 do paper: [0,100] para n<=200, [0,500] para n=500/1000
SIZES_AND_GRIDS = [
    (10, 100),
    (20, 100),
    (50, 100),
    (100, 100),
    (200, 100),
    (500, 500),
    (1000, 500),
]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    seed_counter = 1
    total = 0
    for n, grid in SIZES_AND_GRIDS:
        for i in range(1, N_PER_SIZE + 1):
            name = f"salehipour_n{n:04d}_i{i:02d}"
            instance = generate_dmp_instance(n_nodes=n, grid_size=grid, seed=seed_counter)
            save_as_tsplib(instance, name, out_dir=str(OUT_DIR))
            seed_counter += 1
            total += 1
        print(f"n={n} (grid=[0,{grid}]): {N_PER_SIZE} instancias geradas", file=sys.stderr)

    print(f"Total: {total} instancias salvas em {OUT_DIR}", file=sys.stderr)


if __name__ == "__main__":
    main()
