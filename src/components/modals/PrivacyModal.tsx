import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

interface PrivacyModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const PrivacyModal: React.FC<PrivacyModalProps> = ({ open, onOpenChange }) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Privacy Policy</DialogTitle>
          <DialogDescription>
            Last updated: November 2025
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="h-[60vh] pr-4">
          <div className="space-y-4 text-sm text-foreground/80">
            <section>
              <h3 className="font-semibold text-foreground mb-2">1. Information We Collect</h3>
              <p>We collect information you provide directly to us, including:</p>
              <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                <li>Personal information (name, email, academic details)</li>
                <li>Profile data (GPA, major, interests, background)</li>
                <li>Application tracking data</li>
                <li>Usage data and analytics</li>
              </ul>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">2. How We Use Your Information</h3>
              <p>We use the information we collect to:</p>
              <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                <li>Match you with relevant scholarship opportunities</li>
                <li>Provide personalized recommendations</li>
                <li>Improve our AI matching algorithms</li>
                <li>Send you important updates and notifications</li>
                <li>Analyze usage patterns to improve our service</li>
              </ul>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">3. Information Sharing</h3>
              <p>
                We do not sell your personal information. We may share your information with:
              </p>
              <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                <li>Service providers who assist in platform operations</li>
                <li>Scholarship organizations when you apply through our platform</li>
                <li>Legal authorities when required by law</li>
              </ul>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">4. Data Security</h3>
              <p>
                We implement industry-standard security measures to protect your information, including:
              </p>
              <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                <li>Encryption of data in transit and at rest</li>
                <li>Secure authentication via Firebase</li>
                <li>Regular security audits and updates</li>
                <li>Access controls and monitoring</li>
              </ul>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">5. Your Rights</h3>
              <p>You have the right to:</p>
              <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                <li>Access your personal information</li>
                <li>Request correction of inaccurate data</li>
                <li>Delete your account and associated data</li>
                <li>Export your data</li>
                <li>Opt out of non-essential communications</li>
              </ul>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">6. Cookies and Tracking</h3>
              <p>
                We use cookies and similar technologies to enhance your experience, analyze usage, 
                and provide personalized content. You can control cookie preferences through your browser settings.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">7. Third-Party Services</h3>
              <p>
                Our platform integrates with third-party services including Firebase, Google Gemini AI, 
                and Cloudinary. Each service has its own privacy policy.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">8. Children's Privacy</h3>
              <p>
                ScholarStream is intended for students 13 years and older. We do not knowingly collect 
                information from children under 13.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">9. Changes to Privacy Policy</h3>
              <p>
                We may update this privacy policy periodically. We will notify users of significant changes 
                via email or platform notification.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">10. Contact Us</h3>
              <p>
                For privacy-related questions or to exercise your rights, please contact us through our 
                support channels.
              </p>
            </section>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};
