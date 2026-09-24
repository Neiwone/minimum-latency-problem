# FPmax* (vendored)

Fontes de [FPmax-LIB](https://github.com/marcelorhmaia/FPmax-LIB) (MIT — ver
`LICENSE`), que empacota o FPmax* original de Grahne & Zhu
([FIMI](http://fimi.uantwerpen.be/src)) como biblioteca chamável em memória,
sem I/O de arquivo nem `system()`.

Usado por `src/mdm_gils_rvnd.cpp` para a mineração de itemsets maximais
frequentes de arcos (ver `docs/hypotheses/h13-mdm-gils-rvnd.md`), no lugar
do subprocesso Python (`scripts/fpmax_mine.py` + `mlxtend`) que a primeira
versão usava.

Vendorizado (em vez de submodule/`.so`) para o build continuar sendo um
`make` sem dependência externa em runtime. Compilado com `-DMFI`, como o
CMakeLists do projeto original exige. Nenhuma modificação nos fontes.

Referência de integração: [MDM-HGS-CVRP](https://github.com/marcelorhmaia/MDM-HGS-CVRP)
(`Program/Population.cpp::mineElite`), do mesmo autor — de onde vêm as
convenções de mapear arco `(u,v)` para o item `u*n + v`, `minsup` absoluto
`max(2, frac * |elite|)` e `nlargest` = número de padrões.
