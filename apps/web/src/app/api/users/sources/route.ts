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

export async function PUT(request: NextRequest) {
  try {
    const body = await request.json();
    const { userId, sources } = body;

    if (!userId || !Array.isArray(sources)) {
      return NextResponse.json(
        { error: "Invalid request: userId and sources array are required" },
        { status: 400 }
      );
    }

    const db = getAdminFirestore();
    await db.collection("users").doc(userId).update({ sources });

    return NextResponse.json({ status: "success" });
  } catch (error) {
    console.error("Sources API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
