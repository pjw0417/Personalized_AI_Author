from gutenberg_api import fetch_book_text

groups = {
    "children": [11, 55, 16, 17396, 271],
    "teen": [37106, 74, 120, 45, 215],
    "classics": [98, 74222, 100, 2554, 28054, 2600, 5200],
    "fantasy": [1640, 67090, 17157],
    "science fiction": [62, 84, 5230, 35],
    "mystery": [1661, 2852, 6133],
    "romance": [1260, 1513, 1342, 158],
    "adventure": [521, 1257, 78],
    "philosophical essays": [205, 16643, 1998],
    "academic nonfiction": [34901, 1232, 132],
    "poetry": [1322, 8800, 12242],
    "folklore": [11339, 2591],
    "religion": [10],
}

for shelf, ids in groups.items():
    print(f"\n{shelf}:")
    for book_id in ids:
        try:
            title, _ = fetch_book_text(str(book_id))
            print(f"  {book_id}: {title}")
        except Exception as e:
            print(f"  {book_id}: failed ({e})")

