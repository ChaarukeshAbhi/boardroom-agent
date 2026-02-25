export async function POST(request: NextRequest) {
  try {
    const { meeting_link } = await request.json();

    // Call backend to start Recall.ai recording
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/meetings/start-recording`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ meeting_link }),
      }
    );

    if (!response.ok) {
      return NextResponse.json(
        { error: "Failed to start recording" },
        { status: 400 }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}