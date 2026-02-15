import { NextRequest, NextResponse } from "next/server";
import { initializeApp, cert, getApps } from "firebase-admin/app";
import { getFirestore } from "firebase-admin/firestore";

// Firebase Admin 初期化
function getAdminFirestore() {
  if (getApps().length === 0) {
    if (process.env.NEXT_PUBLIC_USE_EMULATOR === "true") {
      // Emulator接続: FIRESTORE_EMULATOR_HOST を設定
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

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ collectionId: string }> }
) {
  try {
    const { collectionId } = await params;
    const body = await request.json();
    const { articleUrl, rating, comment } = body;

    if (!articleUrl || !rating || rating < 1 || rating > 5) {
      return NextResponse.json(
        { error: "Invalid request: articleUrl and rating (1-5) are required" },
        { status: 400 }
      );
    }

    const db = getAdminFirestore();

    // articleUrl から記事を検索
    const articlesRef = db.collection("articles");
    const snapshot = await articlesRef
      .where("collection_id", "==", collectionId)
      .where("url", "==", articleUrl)
      .limit(1)
      .get();

    if (snapshot.empty) {
      return NextResponse.json(
        { error: "Article not found" },
        { status: 404 }
      );
    }

    const articleDoc = snapshot.docs[0];
    const updateData: Record<string, unknown> = {
      user_rating: rating,
    };
    if (comment) {
      updateData.user_comment = comment;
    }

    await articleDoc.ref.update(updateData);

    return NextResponse.json({ status: "success" });
  } catch (error) {
    console.error("Feedback API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
