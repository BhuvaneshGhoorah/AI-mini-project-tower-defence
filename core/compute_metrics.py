import csv
from collections import defaultdict

runs_needed = 10
data = defaultdict(list)

with open("tower_metrics.csv", "r") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

    for row in rows:  # <-- use rows here
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

    avg_paths_completed = sum(m["paths_completed"] for m in metrics_list) / len(metrics_list)
    avg_nodes_expanded = sum(m["nodes_expanded"] for m in metrics_list) / len(metrics_list)
    avg_path_length = sum(m["total_path_length"] for m in metrics_list) / len(metrics_list)
    avg_paths_attempted = sum(m["paths_attempted"] for m in metrics_list) / len(metrics_list)

    summary.append({
            "algorithm": algo,
            "avg_paths_completed": avg_paths_completed,
            "avg_nodes_expanded": avg_nodes_expanded,
            "avg_path_length": avg_path_length,
            "avg_paths_attempted": avg_paths_attempted
        })

    # Save summary
    with open("metrics_summary.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)

    print("\n✅ Averages saved to metrics_summary.csv")
    print(f"--- {algo} ---")
    print(f"Average paths completed: {avg_paths_completed}")
    print(f"Average nodes expanded: {avg_nodes_expanded}")
    print(f"Average path length: {avg_path_length}")
    print(f"Average paths attempted: {avg_paths_attempted}")
