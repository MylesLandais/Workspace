import { UpyoEmailService } from "./email/upyo-service";
import { EmailService } from "./email/types";

// Export the singleton instance
export const emailService: EmailService = new UpyoEmailService();

// Keep the old function for backward compatibility if needed,
// or rewrite it to use the service.
// Better Auth config used `sendPasswordResetEmail(email, url)`.
export async function sendPasswordResetEmail(email: string, url: string) {
  await emailService.sendPasswordReset(email, url);
}
