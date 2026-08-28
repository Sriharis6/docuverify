import requests
import os
import json

url = "http://127.0.0.1:8000/analyze"

def test_file(file_path):
    print(f"\n==================================================")
    print(f" TESTING: {file_path}")
    print(f"==================================================")
    if not os.path.exists(file_path):
        print("Error: File not found!")
        return
        
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
        
    if response.status_code == 200:
        data = response.json()
        print(f"Overall Suspicion Score: {data.get('overall_score'):.2f} (0=Genuine, 1=Tampered)")
        print(f"Authenticity Confidence: {data.get('authenticity_confidence') * 100:.1f}%")
        print(f"Is Authentic: {'YES (Genuine)' if data.get('is_authentic') else 'NO (Tampered/Suspicious)'}")
        print(f"Flagged Regions Count: {len(data.get('regions', []))}")
        print("\nExplanation Summary:")
        print(data.get('summary'))
        print("\nModule Scores:")
        for mod, res in data.get('module_breakdown', {}).items():
            print(f"  - {mod.upper()}: Score={res.get('score'):.2f}, Flagged={res.get('flagged')}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_files = [
        "dataset/genuine/id_1.jpg",
        "dataset/genuine/id_2.jpg",
        "dataset/tampered/id_1_bad_date.jpg",
        "dataset/tampered/id_2_copy_move.jpg",
        "dataset/tampered/id_3_typography.jpg"
    ]
    for tf in test_files:
        test_file(tf)

