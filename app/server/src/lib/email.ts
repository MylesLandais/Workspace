import { createMessage, type Transport } from "@upyo/core";
import { SmtpTransport } from "@upyo/smtp";
import { MockTransport } from "@upyo/mock";

// 1. Determine which transport to use
const getTransport = (): Transport => {
  if (process.env.NODE_ENV === "test") {
    // Stores emails in memory for assertion
    return new MockTransport();
  }
  
  // Real sending for prod/staging
  return new SmtpTransport({
    host: "smtp.provider.com",
    port: 587,
    auth: { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS }
  });
};

// 2. Export the client
export const mailer = getTransport();

// 3. Helper to send the invite code
export const sendInviteCode = async (email: string, code: string) => {
  await mailer.send(createMessage({
    from: "noreply@your-launch.com",
    to: email,
    subject: "Your Exclusive Invite Code",
    content: {
      text: `Welcome! Your invite code is: ${code}`,
      html: `<p>Welcome! Your invite code is: <strong>${code}</strong></p>`
    }
  }));
};
