import { openai } from "@/lib/openai";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { issue } = body;

    if (!issue || typeof issue !== "string") {
      return NextResponse.json(
        { error: "Please provide an 'issue' field in the request body." },
        { status: 400 }
      );
    }

    const prompt = `Describe the following issue in detail in about 100 words in plaintext without any markdown: ${issue}`;

    const completion = await openai.chat.completions.create({
      model: "gpt-5-nano",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 300,
    });

    const aiResponse = completion.choices[0]?.message.content?.trim() || "";

    return NextResponse.json({ description: aiResponse });
  } catch (error) {
    console.error("OpenAI API error:", error);
    return NextResponse.json(
      { error: "Failed to generate description from OpenAI." },
      { status: 500 }
    );
  }
}
