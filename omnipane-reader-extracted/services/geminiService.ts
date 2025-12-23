import { GoogleGenAI, Type } from "@google/genai";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
const model = "gemini-3-flash-preview";

export const generateArticleSummary = async (content: string, title: string) => {
  const systemInstruction = `
    You are an expert Reading Assistant in a "Single Pane of Glass" feed reader app.
    Your job is to help the user quickly digest content.
    Provide a concise summary and 3 bulleted key takeaways.
    Return JSON.
  `;

  const prompt = `
    Analyze this article:
    Title: ${title}
    Content: ${content}

    Output valid JSON with the following schema:
    {
      "summary": "A 2-3 sentence executive summary.",
      "keyTakeaways": ["Point 1", "Point 2", "Point 3"]
    }
  `;

  try {
    const response = await ai.models.generateContent({
      model,
      contents: prompt,
      config: {
        systemInstruction,
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            summary: { type: Type.STRING },
            keyTakeaways: {
              type: Type.ARRAY,
              items: { type: Type.STRING }
            }
          }
        }
      }
    });

    return JSON.parse(response.text || "{}");
  } catch (error) {
    console.error("AI Summary Error:", error);
    throw new Error("Failed to generate summary");
  }
};

export const chatWithArticle = async (content: string, question: string, history: any[] = []) => {
  // Simple chat without history persistence for this demo, just context injection
  const systemInstruction = `
    You are a helpful assistant answering questions about a specific article the user is reading.
    Only answer based on the provided context. Be brief and conversational.
  `;

  try {
    const response = await ai.models.generateContent({
      model,
      contents: `Context: ${content}\n\nUser Question: ${question}`,
      config: { systemInstruction }
    });
    return response.text;
  } catch (error) {
    console.error("AI Chat Error:", error);
    return "Sorry, I couldn't process that question right now.";
  }
};