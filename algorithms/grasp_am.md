### Algoritmo 1: Atualização do Conjunto Elite

Procedimento $AddElite(S, maxSize)$
1. Se $S \in \text{EliteSet}$
2. $\quad$ Retornar
3. Adicionar $S$ ao $\text{EliteSet}$
4. Ordenar $\text{EliteSet}$ por custo ascendente
5. Se $|\text{EliteSet}| > maxSize$:
6. $\quad \text{Remover a pior solução}$
6. $\text{Recalcular as frequencias}$

---

### Algoritmo 2: Construção com Memória Adaptativa

lambda é a intencidade de confiabilidade na memoria
bonus é projetado para ser consistente: freqNorm é porcentagem que a aresta esta no conjunto de elite; avgDist está la para dar a escala do problema;

Procedimento $Construction\_AM(\alpha, \lambda, \text{EliteSet})$
1. $CL \gets \{1, \dots, n-1\}$, $route \gets \{0\}$, $u \gets 0$
2. Enquanto $CL \neq \emptyset$:
3. $\quad avgDist \gets \frac{1}{|CL|} \sum_{v \in CL} dist(u, v)$
4. $\quad$ Para cada $v \in CL$:
5. $\quad\quad freqNorm \gets \frac{freq[u][v]}{|\text{EliteSet}|}$ (ou $0$ se $|\text{EliteSet}| = 0$)
6. $\quad\quad bonus \gets \lambda \cdot freqNorm \cdot avgDist$
7. $\quad\quad c'(u, v) \gets dist(u, v) - bonus$
8. $\quad c'_{min} \gets \min_{v \in CL} \{c'(u, v)\}$, $c'_{max} \gets \max_{v \in CL} \{c'(u, v)\}$
9. $\quad \tau \gets c'_{min} + \alpha \cdot (c'_{max} - c'_{min})$
10. $\quad RCL \gets \{v \in CL \mid c'(u, v) \leq \tau\}$
11. $\quad v_{next} \gets \text{EscolhaAleatoria}(RCL)$
12. $\quad$ Adicionar $v_{next}$ ao $route$; $u \gets v_{next}$
13. $\quad$ Remover $v_{next}$ de $CL$
14. Retornar $route$

---

### Algoritmo 3: GRASP com Memória Adaptativa

1. $\text{GRASP-AM}(maxIter, poolSize, \lambda, \alpha_{f})$
1. $\text{Initialize EliteSet}$
2. $\text{while i < maxIter - 1}$:
3. $\quad$ $\text{Se }\alpha_{f}\text{ não definido}$:
4. $\quad\quad$ $\alpha \gets \text{random}(0.00, 0.25)$
7. $\quad S \gets \text{Construction-AM}(\alpha, \lambda, \text{EliteSet})$
8. $\quad S \gets \text{RVND}(S)$
9. $\quad \text{AddElite}(S, poolSize)$
10. $\quad$ Se $S.cost < S_{b}.cost$:
11. $\quad\quad S_{b} \gets S$
12. Retornar $S_{b}$