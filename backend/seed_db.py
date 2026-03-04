from pathlib import Path

import chromadb


def get_client():
    project_root = Path(__file__).resolve().parents[1]
    db_path = project_root / "database" / "chroma_data"
    db_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(db_path))


def seed():
    client = get_client()
    collection = client.get_or_create_collection(name="case_kottayam_star")

    documents = [
        "The Kottayam Star prototype chip was secured in Server Rack A. It was confirmed present at 11:30 PM.",
        "Intern Leo's ID badge swiped into the secure server room at 11:30 PM for scheduled backups.",
        "The secure server room door sensor logged the door as 'held open' from 11:40 PM to 11:55 PM.",
        "Leo stated during initial questioning that he locked the door immediately behind him.",
        "Dr. Tara received an email at 5:00 PM stating her funding for the Star project was permanently revoked.",
        "Dr. Tara claims she was grading papers in the faculty lounge from 11:00 PM to midnight.",
        "The faculty lounge motion sensors show zero movement between 10:45 PM and 6:00 AM.",
        "The Kottayam Star chip was discovered missing at 11:55 PM.",
    ]

    ids = [f"evidence_{i}" for i in range(len(documents))]

    collection.add(documents=documents, ids=ids)

    print("Seeded case_kottayam_star with mystery facts.")


if __name__ == "__main__":
    seed()

