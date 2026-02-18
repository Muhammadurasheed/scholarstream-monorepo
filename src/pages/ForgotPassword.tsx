import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { sendPasswordResetEmail } from 'firebase/auth';
import { auth } from '@/lib/firebase';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft, Mail, CheckCircle2 } from 'lucide-react';

const ForgotPassword = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [error, setError] = useState('');

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setError('Email is required');
      return;
    }
    
    if (!validateEmail(email)) {
      setError('Please enter a valid email address');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      await sendPasswordResetEmail(auth, email);
      setEmailSent(true);
      toast({
        title: 'Reset link sent!',
        description: 'Check your email for password reset instructions',
      });
    } catch (error: any) {
      const errorMessages: { [key: string]: string } = {
        'auth/user-not-found': 'No account found with this email address',
        'auth/invalid-email': 'Invalid email address',
        'auth/too-many-requests': 'Too many requests. Please try again later',
      };
      
      const message = errorMessages[error.code] || 'Failed to send reset email. Please try again.';
      setError(message);
      toast({
        title: 'Error',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  if (emailSent) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="max-w-md w-full p-8 text-center">
          <div className="mb-6">
            <div className="h-16 w-16 rounded-full bg-success/20 flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="h-8 w-8 text-success" />
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-2">Check Your Email</h1>
            <p className="text-muted-foreground">
              We've sent password reset instructions to
            </p>
            <p className="font-semibold text-foreground mt-1">{email}</p>
          </div>
          
          <div className="space-y-4">
            <Button onClick={() => navigate('/login')} className="w-full">
              Back to Login
            </Button>
            <Button 
              variant="ghost" 
              onClick={() => setEmailSent(false)}
              className="w-full"
            >
              Try another email
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Button
          variant="ghost"
          className="mb-6"
          onClick={() => navigate('/login')}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Login
        </Button>

        <Card className="p-8">
          <div className="text-center mb-8">
            <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4">
              <Mail className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-2xl font-bold text-foreground mb-2">Reset Password</h1>
            <p className="text-muted-foreground">
              Enter your email and we'll send you reset instructions
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@university.edu"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError('');
                }}
                className={error ? 'border-destructive' : ''}
                autoFocus
              />
              {error && <p className="text-sm text-destructive">{error}</p>}
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Sending...' : 'Send Reset Link'}
            </Button>
          </form>

          <div className="mt-6 text-center text-sm">
            <Link to="/signup" className="text-primary hover:underline">
              Don't have an account? Sign up
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ForgotPassword;
