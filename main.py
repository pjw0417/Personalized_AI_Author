# main.py
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()  # make sure OPENAI_API_KEY is available

from questionnaire import UserProfile
from pipeline import generate_book_for_user
from html_pdf import html_text_to_pdf
from artifact_utils import guess_book_title, make_pdf_path

def main():
    # Example user; later, fill this from a web form or CLI
    profile = UserProfile(
        age=25,
        education_level="Master's in Computer Science",
        preferred_theme="novel",
        purpose_of_reading="self motivation and personal growth",
        mood_today="curious and reflective",
        favorite_author="Ernest Hemingway",
        length_in_pages=2,  # start small while testing
        special_request="I prefer a modern voice with vivid imagery.",
    )

    results = generate_book_for_user(profile)

    # Save intermediate artifacts
    with open("plan.txt", "w", encoding="utf-8") as f:
        f.write(results["plan"])

    with open("draft_raw.txt", "w", encoding="utf-8") as f:
        f.write(results["draft"])

    with open("book_final.txt", "w", encoding="utf-8") as f:
        f.write(results["final_text"])

    with open("critique.txt", "w", encoding="utf-8") as f:
        f.write(results["critique"])

    # Convert final text to PDF, using the derived title as filename
    title = guess_book_title(results.get("plan", ""), results.get("final_text", ""))
    pdf_path = make_pdf_path(Path("."), title)
    html_text_to_pdf(results["final_text"], str(pdf_path))

    print("\n Generation complete.")
    print(f"Files created: plan.txt, draft_raw.txt, book_final.txt, critique.txt, {pdf_path.name}")

if __name__ == "__main__":
    main()
