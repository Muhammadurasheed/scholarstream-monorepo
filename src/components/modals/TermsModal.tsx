import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';

interface TermsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export const TermsModal: React.FC<TermsModalProps> = ({ open, onOpenChange }) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Terms of Service</DialogTitle>
          <DialogDescription>
            Last updated: November 2025
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="h-[60vh] pr-4">
          <div className="space-y-4 text-sm text-foreground/80">
            <section>
              <h3 className="font-semibold text-foreground mb-2">1. Acceptance of Terms</h3>
              <p>
                By accessing and using ScholarStream, you accept and agree to be bound by these Terms of Service. 
                If you do not agree to these terms, please do not use our service.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">2. Service Description</h3>
              <p>
                ScholarStream is a scholarship discovery and application management platform. We provide AI-powered 
                matching algorithms to connect students with relevant scholarship opportunities. We do not guarantee 
                scholarship awards or application success.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">3. User Responsibilities</h3>
              <p>You agree to:</p>
              <ul className="list-disc list-inside ml-4 mt-2 space-y-1">
                <li>Provide accurate and truthful information</li>
                <li>Maintain the security of your account credentials</li>
                <li>Use the service only for lawful purposes</li>
                <li>Not attempt to access unauthorized areas of the platform</li>
                <li>Verify all scholarship information independently before applying</li>
              </ul>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">4. Account Security</h3>
              <p>
                You are responsible for maintaining the confidentiality of your account and password. 
                You agree to notify us immediately of any unauthorized access to your account.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">5. Intellectual Property</h3>
              <p>
                All content, features, and functionality of ScholarStream are owned by us and protected by 
                international copyright, trademark, and other intellectual property laws.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">6. Disclaimer of Warranties</h3>
              <p>
                ScholarStream is provided "as is" without warranties of any kind. We do not guarantee the accuracy, 
                completeness, or timeliness of scholarship information. Users should verify all information with 
                scholarship providers directly.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">7. Limitation of Liability</h3>
              <p>
                We shall not be liable for any indirect, incidental, special, consequential, or punitive damages 
                resulting from your use of or inability to use the service.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">8. Changes to Terms</h3>
              <p>
                We reserve the right to modify these terms at any time. Continued use of the service after changes 
                constitutes acceptance of the new terms.
              </p>
            </section>

            <section>
              <h3 className="font-semibold text-foreground mb-2">9. Contact</h3>
              <p>
                For questions about these Terms of Service, please contact us through our support channels.
              </p>
            </section>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};
