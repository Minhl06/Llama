import base64
import requests
from PIL import Image
import json
import sqlite3
import re


# SYSTEM PROMPT
SYSTEM_PROMPT = """
You are an AI-powered OCR system designed to scan and extract data from golf scorecards.
Your task is to process the scorecard image and output the data in a structured 4x20 grid format. Follow these rules strictly when formatting the output:
Row 1: The name of the golfer(s). Each golfer's name should be positioned at the start of their respective row.
Row 2: The hole numbers, always listed as 1 to 18, followed by a "Total" column.
Row 3: The par values for each hole, followed by a total par value.
Row 4+: Each golfer’s scores for all 18 holes, followed by their total score. Find the total score by adding all of the golfer's scores from all 18 holes together.
If there are multiple golfers, add additional rows for their names and scores.
The hole numbers and par values remain constant across all rows.
If a golfer's name cannot be detected, label them as "Unknown Golfer X" where X is a sequential number.
Ensure numbers are properly aligned in columns for readability.
If any score is missing or illegible, replace it with ? and do not attempt to guess the score.
dont write out the steps it took to add to the database and just output the database.
"""


# IMAGE TO BASE64
def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image to Base64: {e}")
        return None


# OCR USING LLaMA 3.2
def perform_ocr(image_path):
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return None


    try:
        response = requests.post(
            "http://localhost:11434/api/chat",  # Update if needed
            json={
                "model": "llama3.2-vision",
                "messages": [
                    {
                        "role": "user",
                        "content": SYSTEM_PROMPT,
                        "images": [base64_image],
                    },
                ],
            },
            timeout=30
        )
       
        if response.status_code == 200:
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line)
                        content = json_response.get("message", {}).get("content", "")
                        full_response += content
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
            return full_response
        else:
            print(f"Error: {response.status_code}\n{response.text}")
            return None
    except requests.RequestException as e:
        print(f"OCR request error: {e}")
        return None


# PARSE TEXT TO STRUCTURED DATA
def parse_scorecard(text):
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    if len(lines) < 4:
        print("Insufficient rows in OCR output.")
        return []

    header_row = lines[0]  # Likely "Golfer 1", "Golfer 2", etc.
    hole_row = lines[1]
    par_row = lines[2]
    golfer_rows = lines[3:]

    golfers = []
    unknown_counter = 1

    for row in golfer_rows:
        parts = row.strip().split()
        if not parts:
            continue

        name = parts[0]
        if not re.search(r'[a-zA-Z]', name):  # No name detected
            name = f"Unknown Golfer {unknown_counter}"
            unknown_counter += 1

        raw_scores = parts[1:]
        scores = []
        for s in raw_scores[:-1]:  # Skip last one for now (total)
            scores.append(int(s) if s.isdigit() else None)

        total_score = raw_scores[-1]
        total = int(total_score) if total_score.isdigit() else None

        if len(scores) != 18:
            print(f"Skipping {name}: not enough scores ({len(scores)}).")
            continue

        golfers.append({
            "player_name": name,
            "scores": scores,
            "total_score": total
        })

    return golfers


# DATABASE CREATION
def create_database():
    conn = sqlite3.connect("golf_scorecards.db")
    cursor = conn.cursor()


    cursor.execute('''
        CREATE TABLE IF NOT EXISTS golf_scorecards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            score1 INTEGER NOT NULL, score2 INTEGER NOT NULL, score3 INTEGER NOT NULL,
            score4 INTEGER NOT NULL, score5 INTEGER NOT NULL, score6 INTEGER NOT NULL,
            score7 INTEGER NOT NULL, score8 INTEGER NOT NULL, score9 INTEGER NOT NULL,
            score10 INTEGER NOT NULL, score11 INTEGER NOT NULL, score12 INTEGER NOT NULL,
            score13 INTEGER NOT NULL, score14 INTEGER NOT NULL, score15 INTEGER NOT NULL,
            score16 INTEGER NOT NULL, score17 INTEGER NOT NULL, score18 INTEGER NOT NULL,
            total_score INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# INSERT DATA INTO DB
def insert_scorecard(data):
    conn = sqlite3.connect("golf_scorecards.db")
    cursor = conn.cursor()


    cursor.execute('''
        INSERT INTO golf_scorecards (
            player_name, score1, score2, score3, score4, score5, score6, score7, score8, score9,
            score10, score11, score12, score13, score14, score15, score16, score17, score18, total_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data["player_name"], *data["scores"], data["total_score"]))


    conn.commit()
    conn.close()
    print(f"Inserted scorecard for {data['player_name']}.")


# VIEW DATABASE
def view_database():
    conn = sqlite3.connect("golf_scorecards.db")
    cursor = conn.cursor()


    cursor.execute("SELECT * FROM golf_scorecards")
    rows = cursor.fetchall()


    print("\nGolf Scorecards:")
    print("-" * 100)
    print(f"{'ID':<5}{'Player':<20}{'Total':<10}{'Scores (1-18)':<60}")
    print("-" * 100)


    for row in rows:
        player_id = row[0]
        player_name = row[1]
        scores = row[2:20]
        total_score = row[20]
        print(f"{player_id:<5}{player_name:<20}{total_score:<10}{str(scores)}")


    conn.close()


# MAIN LOGIC
def main():
    create_database()
    image_path = "scorecard_golf.jpg"  # Replace with your actual image file path 
    raw_text = perform_ocr(image_path)


    if raw_text:
        print("\n--- OCR Output ---")
        print(raw_text)
        parsed_data = parse_scorecard(raw_text)
        if parsed_data:
           for data in parsed_data_list:
            insert_scorecard(data)
           print("Database updated with OCR-extracted scorecards.")
            
        else:
            print("Failed to parse OCR output.")
    else:
        print("OCR failed or returned empty result.")
    
    



    view_database()


if __name__ == "__main__":
    main()





