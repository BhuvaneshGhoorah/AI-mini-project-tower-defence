import csv
from collections import defaultdict
from statistics import mean, stdev

runs_needed = 12 #12 for each algo, but total is 36.
data = defaultdict(list)

with open("tower_metrics.csv", "r") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

    for row in rows:
        algo = row["algorithm"]
        data[algo].append({
            "paths_completed": int(row["paths_completed"]),
            "nodes_expanded": int(row["nodes_expanded"]),
            "total_path_length": int(row["total_path_length"]),
            "paths_attempted": int(row["paths_attempted"])
        })

summary = []

for algo, metrics_list in data.items():
    if len(metrics_list) < runs_needed:
        print(f"{algo}: Only {len(metrics_list)} runs logged, need {runs_needed} for full average")
        continue

    # Extract lists of values for each metric
    paths_completed_list = [m["paths_completed"] for m in metrics_list]
    nodes_expanded_list = [m["nodes_expanded"] for m in metrics_list]
    path_length_list = [m["total_path_length"] for m in metrics_list]
    paths_attempted_list = [m["paths_attempted"] for m in metrics_list]

    summary.append({
        "algorithm": algo,
        "avg_paths_completed": mean(paths_completed_list),
        "std_paths_completed": stdev(paths_completed_list),
        "avg_nodes_expanded": mean(nodes_expanded_list),
        "std_nodes_expanded": stdev(nodes_expanded_list),
        "avg_path_length": mean(path_length_list),
        "std_path_length": stdev(path_length_list),
        "avg_paths_attempted": mean(paths_attempted_list),
        "std_paths_attempted": stdev(paths_attempted_list)
    })

# Save summary with rounded values
with open("metrics_summary.csv", "w", newline="") as f:
    fieldnames = summary[0].keys()
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in summary:
        writer.writerow({k: round(v, 2) if isinstance(v, float) else v for k, v in row.items()})

print("\n✅ Summary (mean ± std) saved to metrics_summary.csv")
for row in summary:
    print(f"\n--- {row['algorithm']} ---")
    print(f"Paths completed: {row['avg_paths_completed']:.2f} ± {row['std_paths_completed']:.2f}")
    print(f"Nodes expanded: {row['avg_nodes_expanded']:.2f} ± {row['std_nodes_expanded']:.2f}")
    print(f"Path length: {row['avg_path_length']:.2f} ± {row['std_path_length']:.2f}")
    print(f"Paths attempted: {row['avg_paths_attempted']:.2f} ± {row['std_paths_attempted']:.2f}")