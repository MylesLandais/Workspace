import { SMTPConnection } from "@upyo/smtp";
import { logger } from "../lib/logger.js";

interface EmailOptions {
  to: string;
  subject: string;
  html: string;
  text?: string;
  replyTo?: string;
}

class EmailService {
  private connection: SMTPConnection | null = null;
  private isInitialized = false;

  async initialize(): Promise<void> {
    try {
      if (this.isInitialized) return;

      const smtpHost = process.env.SMTP_HOST;
      const smtpPort = parseInt(process.env.SMTP_PORT || "587");
      const smtpUser = process.env.SMTP_USER;
      const smtpPassword = process.env.SMTP_PASSWORD;

      if (!smtpHost || !smtpUser || !smtpPassword) {
        logger.warn(
          "Email service not fully configured. Emails will not be sent."
        );
        return;
      }

      this.connection = new SMTPConnection({
        host: smtpHost,
        port: smtpPort,
        secure: smtpPort === 465,
        auth: {
          user: smtpUser,
          pass: smtpPassword,
        },
      });

      await this.connection.verify();
      this.isInitialized = true;
      logger.info("Email service initialized successfully");
    } catch (error) {
      logger.error("Failed to initialize email service", { error });
      throw error;
    }
  }

  async send(options: EmailOptions): Promise<void> {
    try {
      if (!this.connection) {
        throw new Error("Email service not initialized");
      }

      const from = process.env.SMTP_FROM_EMAIL || "noreply@systemnebula.com";

      await this.connection.sendMail({
        from,
        to: options.to,
        subject: options.subject,
        html: options.html,
        text: options.text || stripHtmlTags(options.html),
        replyTo: options.replyTo,
      });

      logger.info("Email sent successfully", {
        to: options.to,
        subject: options.subject,
      });
    } catch (error) {
      logger.error("Failed to send email", { error, to: options.to });
      throw error;
    }
  }

  async sendInviteCode(email: string, code: string): Promise<void> {
    const inviteLink = `${process.env.APP_URL}/invite?code=${code}`;

    const html = `
      <h2>You're invited to System Nebula!</h2>
      <p>Click the link below to join our community:</p>
      <a href="${inviteLink}" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">
        Accept Invite
      </a>
      <p>Or paste this code: <code>${code}</code></p>
    `;

    await this.send({
      to: email,
      subject: "You're invited to System Nebula",
      html,
    });
  }

  async sendWaitlistConfirmation(email: string): Promise<void> {
    const html = `
      <h2>Thank you for joining the System Nebula waitlist!</h2>
      <p>We're excited to have you on board. We'll notify you as soon as you gain access.</p>
      <p>In the meantime, follow us on social media for updates and sneak peeks.</p>
    `;

    await this.send({
      to: email,
      subject: "Waitlist Confirmation - System Nebula",
      html,
    });
  }
}

function stripHtmlTags(html: string): string {
  return html.replace(/<[^>]*>/g, "");
}

export const emailService = new EmailService();
