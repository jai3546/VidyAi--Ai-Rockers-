import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from lzstring import LZString
from pathlib import Path

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize Gemini 1.5 Flash model
model = genai.GenerativeModel('gemini-1.5-flash')  # Changed to use the flash version

def generate_quiz_prompt(subject, grade, language):
    return f"""Generate exactly 5 multiple choice questions for {subject} for class {grade} students following Indian curriculum in {language}. Return ONLY a JSON array with no additional text.

Each question must follow this exact format:
[
    {{
        "question": "What is...",
        "options": {{"A": "option1", "B": "option2", "C": "option3", "D": "option4"}},
        "correct_answer": "A",
        "explanation": "Brief explanation here",
        "video_url": "URL_PLACEHOLDER"
    }},
    ...
]"""

def generate_quizzes():
    subjects = ['Mathematics', 'Science']
    grades = [5, 10]
    languages = ['English', 'Hindi']
    all_quizzes = {}

    for subject in subjects:
        for grade in grades:
            for language in languages:
                key = f"{subject}_class{grade}_{language.lower()}"
                try:
                    print(f"Generating quiz for {key}...")
                    # Check if API key is available (only for development)
                    if not GOOGLE_API_KEY:
                        print(f"Unable to generate quiz. Please contact support.")
                        continue

                    response = model.generate_content(
                        generate_quiz_prompt(subject, grade, language)
                    )

                    # Check if response has text
                    if not response.text:
                        print(f"Could not generate quiz for {key}. Trying next one...")
                        continue

                    try:
                        quiz_data = json.loads(response.text)
                        if isinstance(quiz_data, list) and len(quiz_data) > 0:
                            all_quizzes[key] = quiz_data
                            print(f"Successfully generated quiz for {key}")
                        else:
                            print(f"Quiz format issue for {key}. Skipping...")
                    except json.JSONDecodeError:
                        print(f"Could not process quiz data for {key}. Skipping...")
                        continue

                except Exception as e:
                    print(f"Could not generate quiz for {key}. Skipping...")
                    continue

    if not all_quizzes:
        raise Exception("No quizzes were successfully generated")

    return all_quizzes

def save_quizzes(quizzes):
    # Create static directory if it doesn't exist
    static_dir = Path('static')
    static_dir.mkdir(exist_ok=True)

    # Compress the JSON data
    json_str = json.dumps(quizzes)
    lz = LZString()
    compressed_data = lz.compressToBase64(json_str)

    # Save compressed data
    quiz_file = static_dir / 'quizzes.json'
    with open(quiz_file, 'w', encoding='utf-8') as f:
        json.dump({'data': compressed_data}, f)

def load_fallback_quizzes():
    """Load pre-generated quizzes as a fallback"""
    fallback_path = Path('static/fallback_quizzes.json')
    if fallback_path.exists():
        try:
            with open(fallback_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    return None

def main():
    print("Generating quizzes...")
    try:
        quizzes = generate_quizzes()
        print("Saving quizzes...")
        save_quizzes(quizzes)
        print("Done! Quizzes saved to static/quizzes.json")

        # Also save a copy as fallback for future use
        fallback_path = Path('static/fallback_quizzes.json')
        with open(fallback_path, 'w', encoding='utf-8') as f:
            json.dump(quizzes, f)

    except Exception as e:
        print("\nUnable to generate new quizzes at this time.")

        # Try to use fallback quizzes
        fallback_quizzes = load_fallback_quizzes()
        if fallback_quizzes:
            print("Using previously generated quizzes instead.")
            save_quizzes(fallback_quizzes)
            print("Done! Quizzes loaded from fallback.")
        else:
            print("No fallback quizzes available.")
            print("Please check your internet connection and try again later.")

if __name__ == "__main__":
    main()

