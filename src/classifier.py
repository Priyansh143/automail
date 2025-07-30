# classifier.py

import json
import re
from logger import logging
# Load the clusters (user-defined categories and keywords)
def load_clusters(path='C:\\Users\\priyansh\\Downloads\\AutoEmail\\config\\clusters.json'):
    with open(path, 'r') as file:
        return json.load(file)

# Clean and prepare email text
def preprocess_email(text):
    return text.lower()

# Classify the email into one of the clusters
def classify_email(subject, body, clusters):
    text = preprocess_email(subject + " " + body)

    for cluster in clusters["clusters"]:  # access the list inside the "clusters" key
        for keyword in cluster["keywords"]:
            if isinstance(keyword, str) and re.search(rf'\b{re.escape(keyword.lower())}\b', text.lower()):
                return cluster["name"]
    
    return "Uncategorized"
