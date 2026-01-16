/**
 * Gemini AI Service
 *
 * Handles interactions with Google's Gemini AI for dashboard widgets
 */

// Temporarily disabled due to @google/genai export issues
// import { GoogleGenerativeAI } from '@google/genai';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
// let genAI: GoogleGenerativeAI | null = null;

export function getGenAI(): null {
  return null;
}

/*
function getGenAI() {
  if (!genAI) {
    const apiKey = process.env.NEXT_PUBLIC_GEMINI_API_KEY || process.env.GEMINI_API_KEY;
    if (!apiKey) {
      console.warn('[Gemini] API key not configured');
      return null;
    }
    genAI = new GoogleGenerativeAI(apiKey);
  }
  return genAI;
}
*/

export async function askGemini(
  prompt: string,
  context?: string,
): Promise<string> {
  try {
    const ai = getGenAI();
    if (!ai) {
      return "Gemini AI is not configured. Please add NEXT_PUBLIC_GEMINI_API_KEY to your environment.";
    }

    // Temporarily disabled due to @google/genai export issues
    // const model = ai.getGenerativeModel({ model: 'gemini-pro' });
    //
    // const fullPrompt = context
    //   ? `Context: ${context}\n\nQuery: ${prompt}`
    //   : prompt;
    //
    // const result = await model.generateContent(fullPrompt);
    // const response = await result.response;
    // const text = response.text();
    //
    // return text;
    return "Gemini AI service temporarily disabled.";
  } catch (error) {
    console.error("[Gemini] Error:", error);
    return `Error communicating with Gemini AI: ${error instanceof Error ? error.message : "Unknown error"}`;
  }
}

export async function generateChartData(topic: string): Promise<{
  labels: string[];
  data: number[];
}> {
  try {
    // Temporarily disabled due to @google/genai export issues
    // const prompt = `Generate realistic mock data for a chart about "${topic}".
    // Return ONLY a JSON object with this exact format:
    // {"labels": ["label1", "label2", ...], "data": [num1, num2, ...]}
    //
    // Provide 7 data points. Make the data plausible and relevant to the topic.
    //
    // const response = await askGemini(prompt);
    //
    // // Extract JSON from response
    // const jsonMatch = response.match(/\{[\s\S]*\}/);
    // if (jsonMatch) {
    //   const parsed = JSON.parse(jsonMatch[0]);
    //   return parsed;
    // }

    // Fallback data
    return {
      labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      data: [65, 59, 80, 81, 56, 55, 40],
    };
  } catch (error) {
    console.error("[Gemini] Chart data generation error:", error);
    return {
      labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
      data: [65, 59, 80, 81, 56, 55, 40],
    };
  }
}

export async function summarizeText(
  text: string,
  maxWords: number = 100,
): Promise<string> {
  // Temporarily disabled due to @google/genai export issues
  // const prompt = `Summarize the following text in ${maxWords} words or less:\n\n${text}`;
  // return askGemini(prompt);
  return `Text summarization temporarily disabled (AI service unavailable).`;
}

export async function generateMermaidDiagram(
  description: string,
): Promise<string> {
  // Temporarily disabled due to @google/genai export issues
  // const prompt = `Generate a Mermaid diagram syntax for: ${description}
  //
  // Return ONLY the mermaid syntax, no explanation. Start directly with the diagram type (graph, sequenceDiagram, etc).`;
  //
  // const response = await askGemini(prompt);
  //
  // // Extract mermaid code block if present
  // const mermaidMatch = response.match(/```mermaid\n([\s\S]*?)\n```/);
  // if (mermaidMatch) {
  //   return mermaidMatch[1];
  // }
  //
  // // Remove any markdown code blocks
  // return response.replace(/```[\s\S]*?```/g, '').trim();
  return "Mermaid diagram generation temporarily disabled (AI service unavailable).";
}
