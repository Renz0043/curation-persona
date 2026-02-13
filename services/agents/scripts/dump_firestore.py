"""Firestore Emulator データダンプ

Usage:
    make e2e-dump
"""

import asyncio
import os

os.environ.setdefault("FIRESTORE_EMULATOR_HOST", "localhost:8080")

from google.cloud import firestore


async def main():
    db = firestore.AsyncClient(project="curation-persona")

    print("=" * 70)
    print("  Firestore Emulator データダンプ")
    print("=" * 70)

    # users
    print("\n--- users ---")
    user_count = 0
    async for doc in db.collection("users").stream():
        user_count += 1
        d = doc.to_dict()
        print(f"  [{doc.id}]")
        for s in d.get("sources", []):
            print(f"    - {s['name']} (type={s['type']}, enabled={s['enabled']})")
        if d.get("interestProfile"):
            print(f"    interestProfile: {d['interestProfile'][:80]}...")
    if user_count == 0:
        print("  (empty)")

    # collections
    print("\n--- collections ---")
    col_count = 0
    async for doc in db.collection("collections").stream():
        col_count += 1
        d = doc.to_dict()
        print(f"\n  [{doc.id}]")
        print(f"    status: {d.get('status')}")
        print(f"    date: {d.get('date')}")
        print(f"    user_id: {d.get('user_id')}")
    if col_count == 0:
        print("  (empty)")

    # articles
    print("\n--- articles ---")
    art_count = 0
    articles_by_collection: dict[str, list[dict]] = {}
    async for doc in db.collection("articles").stream():
        art_count += 1
        d = doc.to_dict()
        col_id = d.get("collection_id", "unknown")
        articles_by_collection.setdefault(col_id, []).append(d)

    if art_count == 0:
        print("  (empty)")
    else:
        for col_id, articles in articles_by_collection.items():
            pickups = [a for a in articles if a.get("is_pickup")]
            scored = [a for a in articles if a.get("scoring_status") == "scored"]
            print(f"\n  [collection: {col_id}]")
            print(
                f"    {len(articles)}件 (scored: {len(scored)}, pickup: {len(pickups)})"
            )

            sorted_a = sorted(
                articles, key=lambda a: a.get("relevance_score", 0), reverse=True
            )
            for i, a in enumerate(sorted_a[:5], 1):
                p = " *PICKUP*" if a.get("is_pickup") else ""
                score = a.get("relevance_score", 0)
                title = a["title"][:45]
                summary_len = len(a.get("summary") or "")
                content_len = len(a.get("content") or "")
                print(f"    [{i}] score={score:.2f} | {title}{p}")
                print(f"        summary: {summary_len}字 / content: {content_len}字")
                if a.get("relevance_reason"):
                    print(f"        reason: {a['relevance_reason'][:60]}")
                if a.get("deep_dive_report"):
                    print(f"        report: {a['deep_dive_report'][:60]}...")
                if a.get("user_rating"):
                    print(f"        rating: {'★' * a['user_rating']}")
            if len(articles) > 5:
                print(f"    ... 他 {len(articles) - 5}件")

    print(f"\n  合計: users={user_count}, collections={col_count}, articles={art_count}")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
