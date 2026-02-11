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
        articles = d.get("articles", [])
        pickups = [a for a in articles if a.get("is_pickup")]
        scored = [a for a in articles if a.get("scoring_status") == "scored"]

        print(f"\n  [{doc.id}]")
        print(f"    status: {d.get('status')}")
        print(f"    date: {d.get('date')}")
        print(f"    articles: {len(articles)}件 (scored: {len(scored)}, pickup: {len(pickups)})")

        if articles:
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
            if len(articles) > 5:
                print(f"    ... 他 {len(articles) - 5}件")
    if col_count == 0:
        print("  (empty)")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
