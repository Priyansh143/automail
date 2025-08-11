import json
import os

CLUSTERS_FILE = 'config\\clusters.json'

def add_new_cluster(cluster_data):
    if not os.path.exists(CLUSTERS_FILE):
        raise FileNotFoundError(f"{CLUSTERS_FILE} not found.")

    with open(CLUSTERS_FILE, "r") as f:
        data = json.load(f)

    # Ensure 'clusters' key exists
    if "clusters" not in data:
        data["clusters"] = []

    # Check if the cluster name already exists
    for cluster in data["clusters"]:
        if cluster["name"].lower() == cluster_data["name"].lower():
            return False, "Cluster already exists."

    # Append the new cluster
    data["clusters"].append({
        "name": cluster_data["name"],
        "keywords": cluster_data["keywords"],
        "auto_reply": cluster_data["auto_reply"]
    })

    # Write back to file
    with open(CLUSTERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

    return True, "Cluster added successfully."

def get_clusters():
    with open(CLUSTERS_FILE, "r") as f:
        data = json.load(f)
    return data.get("clusters", []), data

def delete_cluster(cluster_name):
    clusters, full_data = get_clusters()
    updated_clusters = [c for c in clusters if c["name"] != cluster_name]
    full_data["clusters"] = updated_clusters
    with open(CLUSTERS_FILE, "w") as f:
        json.dump(full_data, f, indent=4)