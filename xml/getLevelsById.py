import sys
import os
import json
import time
import random
import requests


URL = "https://totaljerkface.com/get_level.hw"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:152.0) Gecko/20100101 Firefox/152.0",
    "Accept": "*/*",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://totaljerkface.com/happy-wheels-js/index.tjf",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://totaljerkface.com",
}

OUTPUT_DIR = "levels"
PROGRESS_FILE = "completed.json"

MAX_RETRIES = 8


def load_completed():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return set(json.load(f))

    return set()


def save_completed(completed):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(list(completed), f, indent=2)


def parse_ids(txt_file):
    """
    Read one level ID per line.

    Empty lines and lines beginning with # are ignored.
    """

    ids = []

    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            level_id = line.strip()

            if not level_id:
                continue

            if level_id.startswith("#"):
                continue

            ids.append(level_id)

    return ids


def download_level(session, level_id):

    filename = os.path.join(
        OUTPUT_DIR,
        f"{level_id}.dat"
    )

    if os.path.exists(filename):
        print(f"[SKIP] {level_id} ({filename} already exists)")
        return "exists"

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = session.post(
                URL,
                headers=HEADERS,
                data={
                    "level_id": level_id,
                    "action": "get_record",
                    "ip_tracking": str(random.randint(1000000, 9999999))
                },
                timeout=30
            )

            # Rate limited
            if response.status_code == 429:

                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    wait = int(retry_after)
                else:
                    wait = min(
                        60 * attempt,
                        300
                    )

                print(
                    f"[429] {level_id} - waiting {wait}s "
                    f"(attempt {attempt}/{MAX_RETRIES})"
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            with open(filename, "wb") as f:
                f.write(response.content)

            return True

        except requests.exceptions.RequestException as e:

            wait = min(
                10 * attempt,
                120
            )

            print(
                f"[ERROR] {level_id}: {e}"
            )

            print(
                f"Retrying in {wait}s "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )

            time.sleep(wait)

    return False


def main():

    if len(sys.argv) < 2:
        print(
            "Usage: python getLevels.py file.txt"
        )
        return

    txt_file = sys.argv[1]

    if not os.path.isfile(txt_file):
        print(f"Error: file not found: {txt_file}")
        return

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )

    level_ids = parse_ids(txt_file)

    # Remove duplicate IDs while preserving order
    level_ids = list(dict.fromkeys(level_ids))

    completed = load_completed()

    print(
        f"Found {len(level_ids)} levels"
    )

    print(
        f"Already completed: {len(completed)}"
    )

    session = requests.Session()

    for index, level_id in enumerate(level_ids, 1):

        if level_id in completed:
            print(
                f"[SKIP] {level_id}"
            )
            continue

        print(
            f"[{index}/{len(level_ids)}] Downloading {level_id}"
        )

        result = download_level(
            session,
            level_id
        )

        if result is True:

            completed.add(level_id)
            save_completed(completed)

            print(
                f"[OK] {level_id}"
            )

            # Random delay between requests
            delay = random.uniform(3, 5)
            print(f"Waiting {delay:.1f}s...")
            time.sleep(delay)

        elif result == "exists":

            completed.add(level_id)
            save_completed(completed)

        else:

            print(
                f"[FAILED PERMANENTLY] {level_id}"
            )

    print("Finished.")


if __name__ == "__main__":
    main()