from html_pdf import html_text_to_pdf


def main() -> None:
    sample = """Title: The Quiet Algorithm
Chapter 1: Dawn of Silence
This is a short paragraph to test justified text wrapping and Roman numerals 1), 2), 3).
이거는 한국말 테스트 입니다. 여기에 한글 문장이 포함되어도 제대로 PDF로 변환되는지 확인합니다.
"""

    html_text_to_pdf(sample, "outputs/test_pdf.pdf")
    print("Wrote outputs/test_pdf.pdf")


if __name__ == "__main__":
    main()
