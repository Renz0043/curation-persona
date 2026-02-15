import { NextRequest, NextResponse } from "next/server";

const COLLECTOR_AGENT_URL =
  process.env.COLLECTOR_AGENT_URL || "http://localhost:8001";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { user_id } = body;

    if (!user_id) {
      return NextResponse.json(
        { error: "user_id is required" },
        { status: 400 }
      );
    }

    const res = await fetch(`${COLLECTOR_AGENT_URL}/api/collect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id }),
    });

    if (!res.ok) {
      const errorText = await res.text();
      console.error("Collector Agent error:", errorText);
      return NextResponse.json(
        { error: "Collector Agent request failed" },
        { status: 502 }
      );
    }

    return NextResponse.json({ status: "accepted" });
  } catch (error) {
    console.error("Collect API error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
