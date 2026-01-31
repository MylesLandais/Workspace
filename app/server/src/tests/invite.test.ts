import { describe, it, expect, beforeEach } from "bun:test";
import { mailer, sendInviteCode } from "../lib/email";
import { MockTransport } from "@upyo/mock";

// Access the underlying mock transport to inspect 'sent' emails
const mockTransport = mailer as unknown as MockTransport;

describe("Invite System", () => {
  beforeEach(() => {
    // Clear the outbox before every test
    mockTransport.reset();
  });

  it("should send an email with the invite code", async () => {
    const userEmail = "test@example.com";
    const inviteCode = "INVITE-2026";

    // 1. Run your actual app logic (or call the function directly)
    await sendInviteCode(userEmail, inviteCode);

    // 2. Assert the email was "sent"
    const sentMessages = mockTransport.getSentMessages();
    expect(sentMessages).toHaveLength(1);

    // Check recipient
    // message.recipients is an array of Address objects
    expect(sentMessages[0].recipients[0].address).toBe(userEmail);

    // 3. Extract the code from the email body to verify it matches
    const content = sentMessages[0].content as { text: string; html: string };
    const emailBody = content.text;
    expect(emailBody).toContain(inviteCode);
  });
});
