import { createMessage, type Transport } from "@upyo/core";
import { MockTransport } from "@upyo/mock";
import { EmailService } from "./types";

export class UpyoEmailService implements EmailService {
  private transport: Transport;

  constructor(transport?: Transport) {
    // In a real app, you would switch transports based on env
    // e.g. if (process.env.NODE_ENV === 'production') use SmtpTransport
    this.transport = transport || new MockTransport();
  }

  async sendPasswordReset(email: string, url: string): Promise<void> {
    const message = createMessage({
      from: "noreply@system-nebula.com",
      to: email,
      subject: "Reset your password",
      content: {
        text: `Click the link to reset your password: ${url}`,
        html: `<p>Click the link to reset your password: <a href="${url}">${url}</a></p>`,
      },
    });

    await this.transport.send(message);

    // Logging for manual verification in dev/UAT
    if (process.env.NODE_ENV !== "production") {
      console.log("\n[UpyoEmailService] --- EMAIL SENT ---");
      console.log(`To: ${email}`);
      console.log(`Subject: Reset your password`);
      console.log(`URL: ${url}`);
      console.log("-------------------------------------\n");
    }
  }

  async sendEmailVerification(email: string, url: string): Promise<void> {
    const message = createMessage({
      from: "noreply@system-nebula.com",
      to: email,
      subject: "Verify your email",
      content: {
        text: `Click the link to verify your email: ${url}`,
        html: `<p>Click the link to verify your email: <a href="${url}">${url}</a></p>`,
      },
    });

    await this.transport.send(message);

    if (process.env.NODE_ENV !== "production") {
      console.log("\n[UpyoEmailService] --- EMAIL SENT ---");
      console.log(`To: ${email}`);
      console.log(`Subject: Verify your email`);
      console.log(`URL: ${url}`);
      console.log("-------------------------------------\n");
    }
  }
}
