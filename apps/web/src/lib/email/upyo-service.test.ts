import { describe, it, expect } from "bun:test";
import { UpyoEmailService } from "./upyo-service";
import { MockTransport } from "@upyo/mock";

describe("UpyoEmailService", () => {
  it("should send password reset email", async () => {
    const mockTransport = new MockTransport();
    const service = new UpyoEmailService(mockTransport);

    const email = "test@example.com";
    const url = "http://example.com/reset-password";

    await service.sendPasswordReset(email, url);

    // Check if email was sent using MockTransport's API
    const messages = mockTransport.getSentMessages();
    // console.log("Sent Email Object:", JSON.stringify(messages[0], null, 2));
    expect(messages.length).toBe(1);
    const sentEmail = messages[0];

    expect(sentEmail.recipients[0].address).toBe(email);
    expect(sentEmail.subject).toBe("Reset your password");
    // Text content might need adjustment depending on how createMessage structures it
    // but assuming simple text access or content object
    expect(sentEmail.content.text).toContain(url);
  });

  it("should send verification email", async () => {
    const mockTransport = new MockTransport();
    const service = new UpyoEmailService(mockTransport);

    const email = "verify@example.com";
    const url = "http://example.com/verify";

    await service.sendEmailVerification(email, url);

    const messages = mockTransport.getSentMessages();
    expect(messages.length).toBe(1);
    const sentEmail = messages[0];

    expect(sentEmail.recipients[0].address).toBe(email);
    expect(sentEmail.subject).toBe("Verify your email");
    expect(sentEmail.content.text).toContain(url);
  });
});
