import csv
import matplotlib.pyplot as plt

# Read data
algorithms = []
metrics = {
    "avg_paths_completed": [],
    "avg_nodes_expanded": [],
    "avg_path_length": [],
    "avg_paths_attempted": []
}

with open("metrics_summary.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        algorithms.append(row["algorithm"])
        for key in metrics:
            metrics[key].append(float(row[key]))

# Plot each metric
for metric_name, values in metrics.items():
    plt.figure(figsize=(6, 4))
    plt.bar(algorithms, values, color=["#007acc", "#ffcc00", "#66bb6a", "#ff7043"])
    plt.title(metric_name.replace("_", " ").title())
    plt.xlabel("Algorithm")
    plt.ylabel("Average Value")
    plt.grid(axis="y", linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(f"{metric_name}.png")
    plt.show()

print("✅ Charts generated for all metrics!")
