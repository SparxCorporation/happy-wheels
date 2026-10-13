import argparse
import os
import random
import requests
import time
import xml.etree.ElementTree as ET

URL = "https://totaljerkface.com/get_level.hw"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://totaljerkface.com/happy-wheels-js/index.tjf",
    "Origin": "https://totaljerkface.com",
    "Content-Type": "application/x-www-form-urlencoded"
}

XML_DIR = "xml_pages"
LEVEL_DIR = "levels"

MAX_RETRIES = 8


def fetch_page(session, payload):

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = session.post(
                URL,
                headers=HEADERS,
                data=payload,
                timeout=30
            )

            if response.status_code == 429:

                wait = min(
                    attempt * 30,
                    300
                )

                print(
                    f"[429] Waiting {wait}s "
                    f"(attempt {attempt}/{MAX_RETRIES})"
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            return response.text

        except Exception as e:

            wait = min(
                attempt * 10,
                120
            )

            print(
                f"[ERROR] {e}"
            )

            print(
                f"Retrying in {wait}s..."
            )

            time.sleep(wait)

    raise Exception(
        "Maximum retries exceeded"
    )


def save_xml(xml_text, filename):

    os.makedirs(
        XML_DIR,
        exist_ok=True
    )

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(xml_text)


def extract_ids(xml_text):

    ids = []

    try:

        root = ET.fromstring(xml_text)

        for lv in root.findall(".//lv"):

            level_id = (
                lv.get("id")
                or lv.get("@id")
            )

            if level_id:
                ids.append(level_id)

    except Exception as e:

        print(
            f"XML parse error: {e}"
        )

    return ids


def download_level(session, level_id):

    os.makedirs(
        LEVEL_DIR,
        exist_ok=True
    )

    filename = os.path.join(
        LEVEL_DIR,
        f"{level_id}.dat"
    )

    if os.path.exists(filename):

        print(
            f"[SKIP] {level_id}"
        )

        return

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = session.post(
                URL,
                headers=HEADERS,
                data={
                    "action": "get_record",
                    "level_id": level_id,
                    "ip_tracking": str(
                        random.randint(
                            1000000,
                            9999999
                        )
                    )
                },
                timeout=30
            )

            if response.status_code == 429:

                wait = min(
                    attempt * 30,
                    300
                )

                print(
                    f"[429] {level_id} "
                    f"waiting {wait}s"
                )

                time.sleep(wait)
                continue

            response.raise_for_status()

            with open(
                filename,
                "wb"
            ) as f:

                f.write(
                    response.content
                )

            print(
                f"[OK] {level_id}"
            )

            return

        except Exception as e:

            wait = min(
                attempt * 10,
                120
            )

            print(
                f"[ERROR] {level_id}: {e}"
            )

            print(
                f"Retrying in {wait}s..."
            )

            time.sleep(wait)

    print(
        f"[FAILED] {level_id}"
    )


def download_pages(
    session,
    action,
    start_page,
    end_page,
    sortby,
    uploaded,
    sterm,
    user_id,
    download_levels
):

    os.makedirs(
        XML_DIR,
        exist_ok=True
    )

    for page in range(
        start_page,
        end_page + 1
    ):

        payload = {
            "action": action
        }

        if action == "get_all":

            payload.update({
                "page": page,
                "sortby": sortby,
                "uploaded": uploaded
            })

        elif action in (
            "search_by_name",
            "search_by_user"
        ):

            payload.update({
                "page": page,
                "sterm": sterm
            })

        elif action == "get_pub_by_user":

            payload.update({
                "page": page,
                "user_id": user_id
            })

        print(
            f"[PAGE {page}] Requesting..."
        )

        try:

            xml_text = fetch_page(
                session,
                payload
            )

            filename = (
                f"{XML_DIR}/"
                f"page{page}.xml"
            )

            save_xml(
                xml_text,
                filename
            )

            print(
                f"[OK] Saved {filename}"
            )

            if download_levels:

                ids = extract_ids(
                    xml_text
                )

                print(
                    f"Found {len(ids)} "
                    f"levels on page {page}"
                )

                for index, level_id in enumerate(
                    ids,
                    1
                ):

                    print(
                        f"[{index}/{len(ids)}] "
                        f"{level_id}"
                    )

                    download_level(
                        session,
                        level_id
                    )

                    delay = random.uniform(
                        3,
                        4
                    )

                    print(
                        f"Waiting "
                        f"{delay:.1f}s..."
                    )

                    time.sleep(delay)

        except Exception as e:

            print(
                f"[ERROR] Page "
                f"{page}: {e}"
            )

        delay = random.uniform(
            3,
            4
        )

        print(
            f"Waiting "
            f"{delay:.1f}s "
            f"before next page..."
        )

        time.sleep(delay)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=[
            "get_all",
            "search_by_name",
            "search_by_user",
            "get_pub_by_user"
        ]
    )

    parser.add_argument(
        "--page",
        type=int,
        default=1
    )

    parser.add_argument(
        "--start-page",
        type=int
    )

    parser.add_argument(
        "--end-page",
        type=int
    )

    parser.add_argument(
        "--sortby",
        default="newest"
    )

    parser.add_argument(
        "--uploaded",
        default="all"
    )

    parser.add_argument(
        "--sterm"
    )

    parser.add_argument(
        "--user-id"
    )

    parser.add_argument(
        "--save",
        metavar="FILE"
    )

    parser.add_argument(
        "--download-levels",
        action="store_true"
    )

    args = parser.parse_args()

    session = requests.Session()

    #
    # Multi-page mode
    #
    if (
        args.start_page is not None
        and
        args.end_page is not None
    ):

        download_pages(
            session=session,
            action=args.action,
            start_page=args.start_page,
            end_page=args.end_page,
            sortby=args.sortby,
            uploaded=args.uploaded,
            sterm=args.sterm,
            user_id=args.user_id,
            download_levels=args.download_levels
        )

        return

    #
    # Single-page mode
    #
    payload = {
        "action": args.action
    }

    if args.action == "get_all":

        payload.update({
            "page": args.page,
            "sortby": args.sortby,
            "uploaded": args.uploaded
        })

    elif args.action == "search_by_name":

        if not args.sterm:
            raise Exception(
                "--sterm required"
            )

        payload["sterm"] = args.sterm

    elif args.action == "search_by_user":

        if not args.sterm:
            raise Exception(
                "--sterm required"
            )

        payload["sterm"] = args.sterm

    elif args.action == "get_pub_by_user":

        if not args.user_id:
            raise Exception(
                "--user-id required"
            )

        payload["user_id"] = args.user_id

    xml_text = fetch_page(
        session,
        payload
    )

    if args.save:

        save_xml(
            xml_text,
            args.save
        )

        print(
            f"Saved {args.save}"
        )

    else:

        print(xml_text)

    if args.download_levels:

        ids = extract_ids(
            xml_text
        )

        print(
            f"Found {len(ids)} levels"
        )

        for index, level_id in enumerate(
            ids,
            1
        ):

            print(
                f"[{index}/{len(ids)}] "
                f"{level_id}"
            )

            download_level(
                session,
                level_id
            )

            delay = random.uniform(
                3,
                4
            )

            print(
                f"Waiting "
                f"{delay:.1f}s..."
            )

            time.sleep(delay)


if __name__ == "__main__":
    main()