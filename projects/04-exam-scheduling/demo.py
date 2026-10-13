"""Self-contained demo: colour the conflict graph of a synthetic exam session and draw it.

    pip install networkx matplotlib
    python demo.py
"""
import random

import matplotlib.pyplot as plt
import networkx as nx

random.seed(7)
SUBJECTS = ["Accounting", "Finance", "Marketing", "Statistics", "Law", "Strategy",
            "Economics", "Logistics", "HR", "Ethics", "Data Science", "Audit"]
students = {s: set(random.sample(range(160), random.randint(8, 14))) for s in SUBJECTS}

# Two exams conflict when at least one student sits both.
G = nx.Graph()
G.add_nodes_from(SUBJECTS)
for i, a in enumerate(SUBJECTS):
    for b in SUBJECTS[i + 1:]:
        if students[a] & students[b]:
            G.add_edge(a, b)

colouring = nx.coloring.greedy_color(G, strategy="largest_first")
n_slots = max(colouring.values()) + 1
assert all(colouring[u] != colouring[v] for u, v in G.edges), "two conflicting exams share a slot"
print(f"{G.number_of_nodes()} exams, {G.number_of_edges()} conflicts -> {n_slots} parallel time slots")

palette = ["#4C78A8", "#F58518", "#54A24B", "#E45756", "#72B7B2", "#B279A2"]
fig, ax = plt.subplots(figsize=(9, 6))
pos = nx.spring_layout(G, seed=3, k=1.3)
nx.draw_networkx_edges(G, pos, ax=ax, edge_color="#B0B7C3", width=1.2)
nx.draw_networkx_nodes(G, pos, ax=ax, node_size=3000, linewidths=0,
                       node_color=[palette[colouring[n] % len(palette)] for n in G])
nx.draw_networkx_labels(G, pos, ax=ax, font_size=7, font_color="white", font_weight="bold")
ax.set_title(f"{len(G)} exams, {G.number_of_edges()} student conflicts -> {n_slots} time slots (one colour = one slot)",
             fontsize=11, loc="left")
ax.axis("off")
fig.tight_layout()
fig.savefig("assets/conflict_graph.png", dpi=160)
