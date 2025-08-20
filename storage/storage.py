import csv, os

CSV_FILE = "countries.csv"

def save_country_to_csv(data):
    if not data or "name" not in data:
        return
    
    file_exists = os.path.isfile(CSV_FILE)
    
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data.keys())
        
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)