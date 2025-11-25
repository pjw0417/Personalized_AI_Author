## Quick Abstract
- Personalized book generator that uses a multi-stage LLM pipeline (plan → draft → edit → critique) to craft user-tailored custom texts and render them to PDF, grounded on a Project Gutenberg RAG corpus. 

I believe in power of writing to heal, comfort, inspire and educate. Currently, people need to explore countless books to find messages or contents that resonates with them personally. This project aims to simplify that process by allowing users to generate custom books based on their interests and profile using AI; By leveraging agentic AI, it is designed for users to easily create personalized books or writing that suits their interests and needs.

## Techniques Used
- RAG over Chroma: Gutenberg titles embedded via OpenAI and retrieved during drafting/editing.
- AI Agentic repetition: GPT-5 nano's iterative critique/refine loop to improve drafts.
- Dynamic artifacting: auto-title guessing, sanitized filenames, PDF export of final text.
- Using ReAct style prompting for plan/draft/critique/rewrite stages.

## Requirements
- Python 3.10+ and `pip install -r requirements.txt`.
- Env vars: `OPENAI_API_KEY`, `GUTENBERG_RAPIDAPI_KEY`; optional `GUTENBERG_BOOK_IDS` for custom RAG corpus.

## Setup Steps (for GitHub users)
1) Clone and create a venv: `python -m venv .venv && source .venv/bin/activate` (or `Scripts\\activate` on Windows).  
2) Install deps: `pip install -r requirements.txt`.  
3) Add `.env` with keys, e.g.  
```
OPENAI_API_KEY=sk-...
GUTENBERG_RAPIDAPI_KEY=...
GUTENBERG_BOOK_IDS=11,55,16,17396,271,...
```
4) Build the vector store: `python build_rag_db.py` (pulls IDs from `GUTENBERG_BOOK_IDS` or defaults).  
5) Run the UI: `flask --app app run` 

## Future Improvements
- Add evaluation benchmark for performance evaluation.
- Explore ways to correctly format different languages into PDF.
- Expand genre presets and allow per-book inclusion/exclusion in the form.
- Try multi agent setups or browser useragent for planning/drafting/critique.
- Improving prompting that can create better writing quality

## Current RAG Book Catalog

| Category | Gutenberg ID | Title |
| --- | --- | --- |
| children | 11 | Alice's Adventures in Wonderland |
| children | 55 | The Wonderful Wizard of Oz |
| children | 16 | Peter Pan|
| children | 17396 | The Secret Garden |
| children | 271 | Black Beauty |
| teen | 37106 | Little Women; Or, Meg, Jo, Beth, and Amy |
| teen | 74 | The Adventures of Tom Sawyer, Complete |
| teen | 120 | Treasure Island |
| teen | 45 | Anne of Green Gables |
| teen | 215 | The call of the wild |
| classics | 98 | A Tale of Two Cities |
| classics | 74222 | Demian |
| classics | 100 | The Complete Works of William Shakespeare |
| classics | 2554 | Crime and Punishment |
| classics | 28054 | The Brothers Karamazov |
| classics | 2600 | War and Peace |
| classics | 5200 | Metamorphosis |
| fantasy | 1640 | Lilith: A Romance |
| fantasy | 67090 | The Worm Ouroboros: A Romance |
| fantasy | 17157 | Gulliver's Travels into Several Remote Regions of the World |
| science fiction | 62 | A Princess of Mars |
| science fiction | 84 | Frankenstein; Or, The Modern Prometheus |
| science fiction | 5230 | The Invisible Man: A Grotesque Romance |
| science fiction | 35 | The Time Machine |
| mystery | 1661 | The Adventures of Sherlock Holmes |
| mystery | 2852 | The Hound of the Baskervilles |
| mystery | 6133 | The Extraordinary Adventures of Arsène Lupin, Gentleman-Burglar |
| romance | 1260 | Jane Eyre: An Autobiography |
| romance | 1513 | Romeo and Juliet |
| romance | 1342 | Pride and Prejudice |
| romance | 158 | Emma |
| adventure | 521 | The Life and Adventures of Robinson Crusoe |
| adventure | 1257 | The three musketeers |
| adventure | 78 | Tarzan of the Apes |
| philosophical essays | 205 | Walden, and On The Duty Of Civil Disobedience |
| philosophical essays | 16643 | Essays by Ralph Waldo Emerson |
| philosophical essays | 1998 | Thus Spake Zarathustra: A Book for All and None |
| academic nonfiction | 34901 | On Liberty |
| academic nonfiction | 1232 | The Prince |
| academic nonfiction | 132 | The Art of War |
| poetry | 1322 | Leaves of Grass |
| poetry | 8800 | The divine comedy |
| poetry | 12242 | Poems by Emily Dickinson, Three Series, Complete |
| folklore | 11339 | Aesop's Fables; a new translation |
| folklore | 2591 | Grimms' Fairy Tales |
| religion | 10 | The King James Version of the Bible |
