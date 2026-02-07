/**
 * Interface for the email service.
 *
 * Separates the logic of "what email to send" from the "how to send it" implementation.
 */
export interface EmailService {
  /**
   * Send a password reset email.
   * @param email The recipient's email address.
   * @param url The reset link URL.
   */
  sendPasswordReset(email: string, url: string): Promise<void>;

  /**
   * Send an email verification email.
   * @param email The recipient's email address.
   * @param url The verification link URL.
   */
  sendEmailVerification(email: string, url: string): Promise<void>;
}
