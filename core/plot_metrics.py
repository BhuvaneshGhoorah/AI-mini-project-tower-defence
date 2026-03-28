import csv
import matplotlib.pyplot as plt

# Read data
algorithms = []
metrics = {
    "avg_paths_completed": [],
    "std_paths_completed": [],
    "avg_nodes_expanded": [],
    "std_nodes_expanded": [],
    "avg_path_length": [],
    "std_path_length": [],
    "avg_paths_attempted": [],
    "std_paths_attempted": []
}

with open("metrics_summary.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        algorithms.append(row["algorithm"])
        for key in metrics:
            metrics[key].append(float(row[key]))

''' each bar means, Mean value ± standard deviation
   ─┬─   ← top cap (limits of that range)
    │
    │    ← vertical line (variation range)
    │
   ─┴─   ← bottom cap (limit of that range)
'''
plot_pairs = [
    ("avg_paths_completed", "std_paths_completed"),
    ("avg_nodes_expanded", "std_nodes_expanded"),
    ("avg_path_length", "std_path_length"),
    ("avg_paths_attempted", "std_paths_attempted")
]

colors = ["#007acc", "#ffcc00", "#66bb6a", "#ff7043"]

for i, (avg_key, std_key) in enumerate(plot_pairs):
    plt.figure(figsize=(6, 4))
    plt.bar(
        algorithms,
        metrics[avg_key],
        yerr=metrics[std_key],
        capsize=5,
        color=colors[i % len(colors)],
        alpha=0.8
    )
    plt.title(avg_key.replace("_", " ").title() + " ± Std Dev")
    plt.xlabel("Algorithm")
    plt.ylabel("Value")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(f"{avg_key}.png")
    plt.show()

print("✅ Charts generated with error bars for all metrics!")