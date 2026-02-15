import { NextRequest, NextResponse } from "next/server";
import { initializeApp, cert, getApps } from "firebase-admin/app";
import { getFirestore } from "firebase-admin/firestore";

function getAdminFirestore() {
  if (getApps().length === 0) {
    if (process.env.NEXT_PUBLIC_USE_EMULATOR === "true") {
      process.env.FIRESTORE_EMULATOR_HOST = "localhost:8080";
      initializeApp({
        projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "curation-persona",
      });
    } else {
      initializeApp({
        credential: cert(
          JSON.parse(process.env.FIREBASE_SERVICE_ACCOUNT_KEY || "{}")
        ),
      });
    }
  }
  return getFirestore();
}

const RESEARCHER_AGENT_URL =
  process.env.RESEARCHER_AGENT_URL || "http://localhost:8003";

export async function POST(
  _request: NextRequest,
  { params }: { params: Promise<{ articleId: string }> }
) {
  try {
    const { articleId } = await params;
    const db = getAdminFirestore();

    // 記事ドキュメントを取得
    const articleDoc = await db.collection("articles").doc(articleId).get();
    if (!articleDoc.exists) {
      return NextResponse.json(
        { error: "Article not found" },
        { status: 404 }
      );
    }

    const article = articleDoc.data()!;
    const { collection_id, user_id, url } = article;

    // research_status を pending に楽観的更新、ユーザー依頼 = ピックアップ相当
    await articleDoc.ref.update({ research_status: "pending", is_pickup: true });

    // Researcher Agent にリクエスト
    const res = await fetch(`${RESEARCHER_AGENT_URL}/api/research`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id,
        collection_id,
        article_url: url,
      }),
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error("Researcher Agent error:", errorText);
      return NextResponse.json(
        { error: "Researcher Agent request failed" },
        { status: 502 }
      );
    }

    return NextResponse.json({ status: "accepted" });
  } catch (error) {
    console.error("Research API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
