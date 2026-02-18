import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/hooks/use-toast';
import { doc, getDoc, setDoc } from 'firebase/firestore';
import { db } from '@/lib/firebase';
import { updatePassword, updateEmail, EmailAuthProvider, reauthenticateWithCredential, deleteUser } from 'firebase/auth';
import {
  User, GraduationCap, FileText, Bell, Settings,
  Upload, Download, Trash2, Eye, Award, Calendar,
  Shield, Mail, Lock, AlertTriangle, Plus, Pencil, ExternalLink, Briefcase, Code
} from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface Project {
  id: string;
  title: string;
  description: string;
  techStack: string[];
  url?: string;
  role?: string;
}

interface WorkExperience {
  id: string;
  role: string;
  company: string;
  startDate: string;
  endDate?: string;
  description: string;
  current: boolean;
}

interface UserProfile {
  firstName: string;
  lastName: string;
  academicStatus: string;
  year?: string;
  school: string;
  gpa?: number;
  major: string;
  graduationYear: string;
  background: string[];
  financialNeed?: number;
  interests: string[];
  email?: string;
  phone?: string;
  testScores?: Record<string, number>;
  achievements?: string[];
  country?: string;
  state?: string;
  city?: string;

  // Deep Profile / App Builder (Phase 4)
  bio?: string;
  hardSkills?: string[];
  softSkills?: string[];
  projects?: Project[];
  experience?: WorkExperience[];
  
  // Essays (Phase 4) - Pre-written snippets for common questions
  essays?: {
    personalStatement?: string;
    whyThisOpportunity?: string;
    careerGoals?: string;
    biggestChallenge?: string;
    teamworkExample?: string;
  };
  
  // Social Links
  linkedinUrl?: string;
  githubUrl?: string;
  portfolioUrl?: string;
  twitterHandle?: string;
}

interface NotificationPreferences {
  newMatches: boolean;
  deadlineReminders: boolean;
  statusUpdates: boolean;
  recommendationUpdates: boolean;
  weeklyDigest: boolean;
  tipsAndAdvice: boolean;
  productUpdates: boolean;
  reminderFrequency: 'realtime' | 'daily' | 'weekly';
}

interface Document {
  id: string;
  name: string;
  type: string;
  uploadDate: string;
  fileSize: number;
  url: string;
  usedIn: string[];
}

export default function Profile() {
  const { user } = useAuth();
  const { toast } = useToast();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    newMatches: true,
    deadlineReminders: true,
    statusUpdates: true,
    recommendationUpdates: true,
    weeklyDigest: false,
    tipsAndAdvice: true,
    productUpdates: false,
    reminderFrequency: 'realtime',
  });
  const [documents, setDocuments] = useState<Document[]>([]);
  const [profileStrength, setProfileStrength] = useState(0);
  const [uploading, setUploading] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showEmailDialog, setShowEmailDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Resume Builder State
  const [newHardSkill, setNewHardSkill] = useState('');
  const [newSoftSkill, setNewSoftSkill] = useState('');
  const [showProjectDialog, setShowProjectDialog] = useState(false);
  const [showExperienceDialog, setShowExperienceDialog] = useState(false);
  const [currentProject, setCurrentProject] = useState<Partial<Project>>({});
  const [currentExperience, setCurrentExperience] = useState<Partial<WorkExperience>>({});
  const [techStackInput, setTechStackInput] = useState('');

  // Get initial tab from URL params
  const initialTab = searchParams.get('tab') || 'profile';
  const [activeTab, setActiveTab] = useState(initialTab);

  useEffect(() => {
    loadUserData();
  }, [user]);

  useEffect(() => {
    calculateProfileStrength();
  }, [profile]);

  const loadUserData = async () => {
    if (!user) return;

    setLoading(true);
    try {
      const savedProfile = localStorage.getItem('scholarstream_profile');
      if (savedProfile) {
        setProfile(JSON.parse(savedProfile));
      }

      const prefsDoc = await getDoc(doc(db, 'user_preferences', user.uid));
      if (prefsDoc.exists()) {
        setPreferences(prefsDoc.data() as NotificationPreferences);
      }

      const docsDoc = await getDoc(doc(db, 'user_documents', user.uid));
      if (docsDoc.exists()) {
        setDocuments(docsDoc.data().documents || []);
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateProfileStrength = () => {
    if (!profile) {
      setProfileStrength(0);
      return;
    }

    // Enhanced scoring per Phase 4 masterplan
    const weights = {
      // Core Identity (25%)
      name: { condition: !!profile.firstName && !!profile.lastName, value: 10 },
      contact: { condition: !!profile.email && !!profile.phone, value: 10 },
      location: { condition: !!profile.country || !!profile.city, value: 5 },
      
      // Academic (15%)
      school: { condition: !!profile.school && !!profile.major, value: 10 },
      gpa: { condition: !!profile.gpa, value: 5 },
      
      // Bio & Skills (20%)
      bio: { condition: !!profile.bio && profile.bio.length > 50, value: 10 },
      hardSkills: { condition: (profile.hardSkills?.length || 0) >= 3, value: 5 },
      softSkills: { condition: (profile.softSkills?.length || 0) >= 2, value: 5 },
      
      // Portfolio (25%) - Weighted heavily for hackathons
      projects: { condition: (profile.projects?.length || 0) >= 1, value: 15 },
      experience: { condition: (profile.experience?.length || 0) >= 1, value: 10 },
      
      // Essays & Extras (15%)
      essays: { condition: !!profile.essays?.personalStatement, value: 10 },
      social: { condition: !!profile.linkedinUrl || !!profile.githubUrl, value: 5 },
    };

    let strength = 0;
    Object.values(weights).forEach(check => {
      if (check.condition) strength += check.value;
    });

    setProfileStrength(strength);
  };

  const saveProfile = async () => {
    if (!user || !profile) return;

    setSaving(true);
    try {
      localStorage.setItem('scholarstream_profile', JSON.stringify(profile));

      await setDoc(doc(db, 'users', user.uid), {
        ...profile,
        updatedAt: new Date().toISOString(),
      }, { merge: true });

      toast({
        title: 'Profile updated',
        description: 'Your changes have been saved successfully.',
      });
    } catch (error) {
      console.error('Error saving profile:', error);
      toast({
        title: 'Error',
        description: 'Failed to save profile. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const savePreferences = async () => {
    if (!user) return;

    try {
      await setDoc(doc(db, 'user_preferences', user.uid), preferences);
      toast({
        title: 'Preferences saved',
        description: 'Your notification preferences have been updated.',
      });
    } catch (error) {
      console.error('Error saving preferences:', error);
      toast({
        title: 'Error',
        description: 'Failed to save preferences.',
        variant: 'destructive',
      });
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !user) return;

    if (file.size > 10 * 1024 * 1024) {
      toast({
        title: 'File too large',
        description: 'Please upload a file smaller than 10MB.',
        variant: 'destructive',
      });
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('upload_preset', 'scholarstream_docs');

      const cloudName = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME || 'demo';
      const response = await fetch(
        `https://api.cloudinary.com/v1_1/${cloudName}/auto/upload`,
        {
          method: 'POST',
          body: formData,
        }
      );

      const data = await response.json();

      const newDoc: Document = {
        id: crypto.randomUUID(),
        name: file.name,
        type: file.type.split('/')[1]?.toUpperCase() || 'FILE',
        uploadDate: new Date().toISOString(),
        fileSize: file.size,
        url: data.secure_url,
        usedIn: [],
      };

      const updatedDocs = [...documents, newDoc];
      setDocuments(updatedDocs);

      await setDoc(doc(db, 'user_documents', user.uid), {
        documents: updatedDocs,
      });

      toast({
        title: 'Document uploaded',
        description: 'Your document has been uploaded successfully.',
      });
    } catch (error) {
      console.error('Error uploading document:', error);
      toast({
        title: 'Upload failed',
        description: 'Failed to upload document. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const deleteDocument = async (docId: string) => {
    if (!user) return;

    try {
      const updatedDocs = documents.filter(doc => doc.id !== docId);
      setDocuments(updatedDocs);

      await setDoc(doc(db, 'user_documents', user.uid), {
        documents: updatedDocs,
      });

      toast({
        title: 'Document deleted',
        description: 'Document removed successfully.',
      });
    } catch (error) {
      console.error('Error deleting document:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete document.',
        variant: 'destructive',
      });
    }
  };

  const handleChangePassword = async () => {
    if (!user || !currentPassword || !newPassword) return;

    if (newPassword !== confirmPassword) {
      toast({
        title: 'Passwords do not match',
        description: 'Please ensure both passwords are the same.',
        variant: 'destructive',
      });
      return;
    }

    if (newPassword.length < 6) {
      toast({
        title: 'Password too short',
        description: 'Password must be at least 6 characters.',
        variant: 'destructive',
      });
      return;
    }

    try {
      const credential = EmailAuthProvider.credential(user.email!, currentPassword);
      await reauthenticateWithCredential(user as any, credential);
      await updatePassword(user as any, newPassword);

      setShowPasswordDialog(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');

      toast({
        title: 'Password updated',
        description: 'Your password has been changed successfully.',
      });
    } catch (error: any) {
      console.error('Error changing password:', error);
      toast({
        title: 'Error',
        description: error.code === 'auth/wrong-password'
          ? 'Current password is incorrect.'
          : 'Failed to change password.',
        variant: 'destructive',
      });
    }
  };

  const handleChangeEmail = async () => {
    if (!user || !newEmail || !currentPassword) return;

    try {
      const credential = EmailAuthProvider.credential(user.email!, currentPassword);
      await reauthenticateWithCredential(user as any, credential);
      await updateEmail(user as any, newEmail);

      setShowEmailDialog(false);
      setNewEmail('');
      setCurrentPassword('');

      toast({
        title: 'Email updated',
        description: 'Your email has been changed successfully.',
      });
    } catch (error: any) {
      console.error('Error changing email:', error);
      toast({
        title: 'Error',
        description: error.code === 'auth/email-already-in-use'
          ? 'This email is already in use.'
          : 'Failed to change email.',
        variant: 'destructive',
      });
    }
  };

  const handleExportData = async () => {
    if (!user) return;

    try {
      const userData = {
        profile,
        preferences,
        documents: documents.map(doc => ({ ...doc, url: '[REDACTED]' })),
        exportDate: new Date().toISOString(),
      };

      const dataStr = JSON.stringify(userData, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `scholarstream-data-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);

      toast({
        title: 'Data exported',
        description: 'Your data has been downloaded successfully.',
      });
    } catch (error) {
      console.error('Error exporting data:', error);
      toast({
        title: 'Error',
        description: 'Failed to export data.',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteAccount = async () => {
    if (!user) return;

    try {
      await deleteUser(user as any);

      toast({
        title: 'Account deleted',
        description: 'Your account has been permanently deleted.',
      });
    } catch (error: any) {
      console.error('Error deleting account:', error);
      toast({
        title: 'Error',
        description: error.code === 'auth/requires-recent-login'
          ? 'Please log out and log back in before deleting your account.'
          : 'Failed to delete account.',
        variant: 'destructive',
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <Skeleton className="h-12 w-64 mb-8" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Profile Settings</h1>
          <p className="text-muted-foreground">
            Manage your account, preferences, and documents
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          <div className="flex-1">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="profile">
                  <User className="w-4 h-4 mr-2" />
                  Profile
                </TabsTrigger>
                <TabsTrigger value="resume">
                  <GraduationCap className="w-4 h-4 mr-2" />
                  CV Builder
                </TabsTrigger>
                <TabsTrigger value="documents">
                  <FileText className="w-4 h-4 mr-2" />
                  Documents
                </TabsTrigger>
                <TabsTrigger value="notifications">
                  <Bell className="w-4 h-4 mr-2" />
                  Notifications
                </TabsTrigger>
                <TabsTrigger value="account">
                  <Settings className="w-4 h-4 mr-2" />
                  Account
                </TabsTrigger>
              </TabsList>

              <TabsContent value="profile" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Personal Information</CardTitle>
                    <CardDescription>
                      Update your basic information and contact details
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="firstName">First Name</Label>
                        <Input
                          id="firstName"
                          value={profile?.firstName || ''}
                          onChange={(e) => setProfile(prev => prev ? { ...prev, firstName: e.target.value } : null)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="lastName">Last Name</Label>
                        <Input
                          id="lastName"
                          value={profile?.lastName || ''}
                          onChange={(e) => setProfile(prev => prev ? { ...prev, lastName: e.target.value } : null)}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="email">Email</Label>
                        <Input
                          id="email"
                          type="email"
                          value={profile?.email || user?.email || ''}
                          onChange={(e) => setProfile(prev => prev ? { ...prev, email: e.target.value } : null)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="phone">Phone Number</Label>
                        <Input
                          id="phone"
                          type="tel"
                          value={profile?.phone || ''}
                          onChange={(e) => setProfile(prev => prev ? { ...prev, phone: e.target.value } : null)}
                          placeholder="(555) 123-4567"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="country">Country</Label>
                        <Input
                          id="country"
                          value={profile?.country || ''}
                          onChange={(e) => setProfile(prev => prev ? { ...prev, country: e.target.value } : null)}
                          placeholder="United States"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="state">State / Province</Label>
                        <Input
                          id="state"
                          value={profile?.state || ''}
                          onChange={(e) => setProfile(prev => prev ? { ...prev, state: e.target.value } : null)}
                          placeholder="NY"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="city">City</Label>
                        <Input
                          id="city"
                          value={profile?.city || ''}
                          onChange={(e) => setProfile(prev => prev ? { ...prev, city: e.target.value } : null)}
                          placeholder="New York"
                        />
                      </div>
                    </div>

                    <Button onClick={saveProfile} disabled={saving}>
                      {saving ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="resume" className="space-y-6">
                <div className="grid gap-6 md:grid-cols-2">
                  <Card className="md:col-span-2">
                    <CardHeader>
                      <CardTitle>Professional Bio</CardTitle>
                      <CardDescription>
                        A short summary of your professional goals and background. Used by the AI for auto-filling "Tell us about yourself".
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <Label>Bio / Summary</Label>
                        <textarea
                          className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                          placeholder="I am a Computer Science student passionate about..."
                          value={profile?.bio || ''}
                          onChange={(e) => setProfile(prev => prev ? { ...prev, bio: e.target.value } : null)}
                        />
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Hard Skills</CardTitle>
                      <CardDescription>Technical languages and tools (e.g., Python, React)</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex gap-2">
                        <Input
                          placeholder="Add skill..."
                          value={newHardSkill}
                          onChange={(e) => setNewHardSkill(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              if (newHardSkill.trim()) {
                                setProfile(prev => prev ? { ...prev, hardSkills: [...(prev.hardSkills || []), newHardSkill.trim()] } : null);
                                setNewHardSkill('');
                              }
                            }
                          }}
                        />
                        <Button onClick={() => {
                          if (newHardSkill.trim()) {
                            setProfile(prev => prev ? { ...prev, hardSkills: [...(prev.hardSkills || []), newHardSkill.trim()] } : null);
                            setNewHardSkill('');
                          }
                        }} size="sm">Add</Button>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {profile?.hardSkills?.map((skill, i) => (
                          <Badge key={i} variant="secondary" className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                            onClick={() => setProfile(prev => prev ? { ...prev, hardSkills: prev.hardSkills?.filter((_, idx) => idx !== i) } : null)}
                          >
                            {skill} &times;
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Soft Skills</CardTitle>
                      <CardDescription>Interpersonal and leadership skills (e.g., Leadership, Communication)</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex gap-2">
                        <Input
                          placeholder="Add skill..."
                          value={newSoftSkill}
                          onChange={(e) => setNewSoftSkill(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              if (newSoftSkill.trim()) {
                                setProfile(prev => prev ? { ...prev, softSkills: [...(prev.softSkills || []), newSoftSkill.trim()] } : null);
                                setNewSoftSkill('');
                              }
                            }
                          }}
                        />
                        <Button onClick={() => {
                          if (newSoftSkill.trim()) {
                            setProfile(prev => prev ? { ...prev, softSkills: [...(prev.softSkills || []), newSoftSkill.trim()] } : null);
                            setNewSoftSkill('');
                          }
                        }} size="sm">Add</Button>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {profile?.softSkills?.map((skill, i) => (
                          <Badge key={i} variant="outline" className="cursor-pointer hover:bg-destructive hover:text-destructive-foreground"
                            onClick={() => setProfile(prev => prev ? { ...prev, softSkills: prev.softSkills?.filter((_, idx) => idx !== i) } : null)}
                          >
                            {skill} &times;
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  {/* Projects Section */}
                  <Card className="md:col-span-2">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="flex items-center gap-2">
                            <Code className="w-5 h-5" />
                            Project Portfolio
                          </CardTitle>
                          <CardDescription>
                            Add detailed projects to power the AI's "Experience" mapping.
                          </CardDescription>
                        </div>
                        <Button onClick={() => {
                          setCurrentProject({});
                          setTechStackInput('');
                          setShowProjectDialog(true);
                        }} size="sm">
                          <Plus className="w-4 h-4 mr-1" /> Add Project
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {(!profile?.projects || profile.projects.length === 0) ? (
                        <div className="text-center py-8 border-2 border-dashed rounded-lg">
                          <Code className="w-10 h-10 mx-auto mb-3 text-muted-foreground" />
                          <p className="text-sm text-muted-foreground mb-2">No projects added yet</p>
                          <Button variant="outline" size="sm" onClick={() => {
                            setCurrentProject({});
                            setTechStackInput('');
                            setShowProjectDialog(true);
                          }}>
                            <Plus className="w-4 h-4 mr-1" /> Add Your First Project
                          </Button>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {profile.projects.map((project) => (
                            <div key={project.id} className="p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <h4 className="font-semibold">{project.title}</h4>
                                    {project.url && (
                                      <a href={project.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                        <ExternalLink className="w-4 h-4" />
                                      </a>
                                    )}
                                  </div>
                                  {project.role && (
                                    <p className="text-sm text-muted-foreground">{project.role}</p>
                                  )}
                                  <p className="text-sm mt-2">{project.description}</p>
                                  <div className="flex flex-wrap gap-1 mt-2">
                                    {project.techStack?.map((tech, i) => (
                                      <Badge key={i} variant="secondary" className="text-xs">{tech}</Badge>
                                    ))}
                                  </div>
                                </div>
                                <div className="flex gap-1">
                                  <Button variant="ghost" size="icon" onClick={() => {
                                    setCurrentProject(project);
                                    setTechStackInput(project.techStack?.join(', ') || '');
                                    setShowProjectDialog(true);
                                  }}>
                                    <Pencil className="w-4 h-4" />
                                  </Button>
                                  <Button variant="ghost" size="icon" onClick={() => {
                                    setProfile(prev => prev ? {
                                      ...prev,
                                      projects: prev.projects?.filter(p => p.id !== project.id)
                                    } : null);
                                  }}>
                                    <Trash2 className="w-4 h-4 text-destructive" />
                                  </Button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Work Experience Section */}
                  <Card className="md:col-span-2">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="flex items-center gap-2">
                            <Briefcase className="w-5 h-5" />
                            Work Experience
                          </CardTitle>
                          <CardDescription>
                            Add internships, jobs, and volunteer work.
                          </CardDescription>
                        </div>
                        <Button onClick={() => {
                          setCurrentExperience({});
                          setShowExperienceDialog(true);
                        }} size="sm">
                          <Plus className="w-4 h-4 mr-1" /> Add Experience
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      {(!profile?.experience || profile.experience.length === 0) ? (
                        <div className="text-center py-8 border-2 border-dashed rounded-lg">
                          <Briefcase className="w-10 h-10 mx-auto mb-3 text-muted-foreground" />
                          <p className="text-sm text-muted-foreground mb-2">No experience added yet</p>
                          <Button variant="outline" size="sm" onClick={() => {
                            setCurrentExperience({});
                            setShowExperienceDialog(true);
                          }}>
                            <Plus className="w-4 h-4 mr-1" /> Add Your First Experience
                          </Button>
                        </div>
                      ) : (
                        <div className="space-y-4">
                          {profile.experience.map((exp) => (
                            <div key={exp.id} className="p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <h4 className="font-semibold">{exp.role}</h4>
                                    {exp.current && (
                                      <Badge variant="default" className="text-xs">Current</Badge>
                                    )}
                                  </div>
                                  <p className="text-sm text-muted-foreground">{exp.company}</p>
                                  <p className="text-xs text-muted-foreground mt-1">
                                    {exp.startDate} — {exp.current ? 'Present' : exp.endDate}
                                  </p>
                                  <p className="text-sm mt-2">{exp.description}</p>
                                </div>
                                <div className="flex gap-1">
                                  <Button variant="ghost" size="icon" onClick={() => {
                                    setCurrentExperience(exp);
                                    setShowExperienceDialog(true);
                                  }}>
                                    <Pencil className="w-4 h-4" />
                                  </Button>
                                  <Button variant="ghost" size="icon" onClick={() => {
                                    setProfile(prev => prev ? {
                                      ...prev,
                                      experience: prev.experience?.filter(e => e.id !== exp.id)
                                    } : null);
                                  }}>
                                    <Trash2 className="w-4 h-4 text-destructive" />
                                  </Button>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  {/* Essays Section (Phase 4) */}
                  <Card className="md:col-span-2">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <FileText className="w-5 h-5" />
                        Essay Snippets
                      </CardTitle>
                      <CardDescription>
                        Pre-write common essay responses. The AI will adapt these to each application.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <Label>Personal Statement / About Me</Label>
                        <textarea
                          className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          placeholder="Tell us about yourself, your background, and what drives you..."
                          value={profile?.essays?.personalStatement || ''}
                          onChange={(e) => setProfile(prev => prev ? { 
                            ...prev, 
                            essays: { ...prev.essays, personalStatement: e.target.value } 
                          } : null)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Career Goals</Label>
                        <textarea
                          className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          placeholder="Where do you see yourself in 5-10 years? What impact do you want to make?"
                          value={profile?.essays?.careerGoals || ''}
                          onChange={(e) => setProfile(prev => prev ? { 
                            ...prev, 
                            essays: { ...prev.essays, careerGoals: e.target.value } 
                          } : null)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Biggest Challenge Overcome</Label>
                        <textarea
                          className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          placeholder="Describe a significant challenge you faced and how you overcame it..."
                          value={profile?.essays?.biggestChallenge || ''}
                          onChange={(e) => setProfile(prev => prev ? { 
                            ...prev, 
                            essays: { ...prev.essays, biggestChallenge: e.target.value } 
                          } : null)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Teamwork Example</Label>
                        <textarea
                          className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          placeholder="Describe a time you worked effectively in a team..."
                          value={profile?.essays?.teamworkExample || ''}
                          onChange={(e) => setProfile(prev => prev ? { 
                            ...prev, 
                            essays: { ...prev.essays, teamworkExample: e.target.value } 
                          } : null)}
                        />
                      </div>
                    </CardContent>
                  </Card>

                  {/* Social Links (Phase 4) */}
                  <Card className="md:col-span-2">
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <ExternalLink className="w-5 h-5" />
                        Social & Portfolio Links
                      </CardTitle>
                      <CardDescription>
                        Add your professional profiles for auto-filling URL fields.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label>LinkedIn URL</Label>
                          <Input
                            placeholder="https://linkedin.com/in/yourprofile"
                            value={profile?.linkedinUrl || ''}
                            onChange={(e) => setProfile(prev => prev ? { ...prev, linkedinUrl: e.target.value } : null)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>GitHub URL</Label>
                          <Input
                            placeholder="https://github.com/yourusername"
                            value={profile?.githubUrl || ''}
                            onChange={(e) => setProfile(prev => prev ? { ...prev, githubUrl: e.target.value } : null)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Portfolio Website</Label>
                          <Input
                            placeholder="https://yourportfolio.com"
                            value={profile?.portfolioUrl || ''}
                            onChange={(e) => setProfile(prev => prev ? { ...prev, portfolioUrl: e.target.value } : null)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label>Twitter/X Handle</Label>
                          <Input
                            placeholder="@yourusername"
                            value={profile?.twitterHandle || ''}
                            onChange={(e) => setProfile(prev => prev ? { ...prev, twitterHandle: e.target.value } : null)}
                          />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
                <div className="flex justify-end">
                  <Button onClick={saveProfile} disabled={saving} size="lg" className="w-full md:w-auto">
                    {saving ? 'Saving Profile DNA...' : 'Save DNA'}
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="documents" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Documents Library</CardTitle>
                    <CardDescription>
                      Manage your reusable documents for scholarship applications
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <input
                        ref={fileInputRef}
                        type="file"
                        className="hidden"
                        accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                        onChange={handleFileUpload}
                      />
                      <Button
                        className="w-full"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={uploading}
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        {uploading ? 'Uploading...' : 'Upload New Document'}
                      </Button>

                      {documents.length === 0 ? (
                        <div className="text-center py-12 border-2 border-dashed rounded-lg">
                          <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                          <p className="text-lg font-medium mb-2">No documents yet</p>
                          <p className="text-sm text-muted-foreground mb-4">
                            Upload documents to reuse them across applications
                          </p>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {documents.map((doc) => (
                            <Card key={doc.id}>
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-3">
                                    <FileText className="w-5 h-5 text-primary" />
                                    <div>
                                      <p className="font-medium">{doc.name}</p>
                                      <p className="text-sm text-muted-foreground">
                                        {doc.type} • {(doc.fileSize / 1024).toFixed(1)} KB • {new Date(doc.uploadDate).toLocaleDateString()}
                                      </p>
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      onClick={() => window.open(doc.url, '_blank')}
                                    >
                                      <Eye className="w-4 h-4" />
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      onClick={() => {
                                        const link = document.createElement('a');
                                        link.href = doc.url;
                                        link.download = doc.name;
                                        link.click();
                                      }}
                                    >
                                      <Download className="w-4 h-4" />
                                    </Button>
                                    <Button
                                      variant="ghost"
                                      size="icon"
                                      onClick={() => deleteDocument(doc.id)}
                                    >
                                      <Trash2 className="w-4 h-4" />
                                    </Button>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="notifications" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Email Notifications</CardTitle>
                    <CardDescription>
                      Choose what updates you want to receive
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>New Scholarship Matches</Label>
                        <p className="text-sm text-muted-foreground">
                          Get notified when we find scholarships that match your profile
                        </p>
                      </div>
                      <Switch
                        checked={preferences.newMatches}
                        onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, newMatches: checked }))}
                      />
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Deadline Reminders</Label>
                        <p className="text-sm text-muted-foreground">
                          Reminders at 7 days, 3 days, and 1 day before deadlines
                        </p>
                      </div>
                      <Switch
                        checked={preferences.deadlineReminders}
                        onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, deadlineReminders: checked }))}
                      />
                    </div>

                    <Separator />

                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>Application Status Updates</Label>
                        <p className="text-sm text-muted-foreground">
                          Updates on your application status and decisions
                        </p>
                      </div>
                      <Switch
                        checked={preferences.statusUpdates}
                        onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, statusUpdates: checked }))}
                      />
                    </div>

                    <Separator />

                    <div className="space-y-2">
                      <Label>Notification Frequency</Label>
                      <Select
                        value={preferences.reminderFrequency}
                        onValueChange={(value: 'realtime' | 'daily' | 'weekly') =>
                          setPreferences(prev => ({ ...prev, reminderFrequency: value }))
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="realtime">Real-time</SelectItem>
                          <SelectItem value="daily">Daily Digest</SelectItem>
                          <SelectItem value="weekly">Weekly Summary</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <Button onClick={savePreferences}>
                      Save Preferences
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="account" className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Account Information</CardTitle>
                    <CardDescription>
                      Manage your account security and preferences
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label>Email Address</Label>
                      <div className="flex gap-2">
                        <Input value={user?.email || ''} disabled />
                        <Button variant="outline" onClick={() => setShowEmailDialog(true)}>
                          <Mail className="w-4 h-4 mr-2" />
                          Change
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label>Password</Label>
                      <Button
                        variant="outline"
                        className="w-full justify-start"
                        onClick={() => setShowPasswordDialog(true)}
                      >
                        <Lock className="w-4 h-4 mr-2" />
                        Change Password
                      </Button>
                    </div>

                    <div className="space-y-2">
                      <Label>Two-Factor Authentication</Label>
                      <Button variant="outline" className="w-full justify-start" disabled>
                        <Shield className="w-4 h-4 mr-2" />
                        Enable 2FA (Coming Soon)
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Privacy & Data</CardTitle>
                    <CardDescription>
                      Control your data and privacy settings
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <Button
                      variant="outline"
                      className="w-full justify-start"
                      onClick={handleExportData}
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Export My Data
                    </Button>
                  </CardContent>
                </Card>

                <Card className="border-destructive">
                  <CardHeader>
                    <CardTitle className="text-destructive">Danger Zone</CardTitle>
                    <CardDescription>
                      Irreversible account actions
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button
                      variant="destructive"
                      className="w-full"
                      onClick={() => setShowDeleteDialog(true)}
                    >
                      <AlertTriangle className="w-4 h-4 mr-2" />
                      Delete Account
                    </Button>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </div>

          <div className="w-full lg:w-80 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Profile Strength</CardTitle>
                <CardDescription>
                  Complete profiles get 40% more matches
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-col items-center">
                  <div className="relative w-32 h-32 mb-4">
                    <svg className="w-full h-full" viewBox="0 0 100 100">
                      <circle
                        className="text-muted stroke-current"
                        strokeWidth="10"
                        cx="50"
                        cy="50"
                        r="40"
                        fill="transparent"
                      />
                      <circle
                        className="text-primary stroke-current"
                        strokeWidth="10"
                        strokeLinecap="round"
                        cx="50"
                        cy="50"
                        r="40"
                        fill="transparent"
                        strokeDasharray={`${profileStrength * 2.51} 251`}
                        transform="rotate(-90 50 50)"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-3xl font-bold">{profileStrength}%</span>
                    </div>
                  </div>
                  <h4 className="text-lg font-semibold mb-2">To improve your score:</h4>
                  <ul className="space-y-1 text-sm text-muted-foreground">
                    {(!profile?.bio || profile.bio.length < 50) && <li>• Add a bio (+10%)</li>}
                    {(!profile?.projects || profile.projects.length === 0) && <li>• Add a project (+15%)</li>}
                    {(!profile?.experience || profile.experience.length === 0) && <li>• Add experience (+10%)</li>}
                    {(!profile?.hardSkills || profile.hardSkills.length < 3) && <li>• Add 3+ hard skills (+5%)</li>}
                    {!profile?.essays?.personalStatement && <li>• Write personal statement (+10%)</li>}
                    {(!profile?.linkedinUrl && !profile?.githubUrl) && <li>• Add social links (+5%)</li>}
                  </ul>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Quick Stats</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Member Since</span>
                  <span className="font-medium">Dec 2025</span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Applications</span>
                  <span className="font-medium">0</span>
                </div>
                <Separator />
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Won</span>
                  <Badge className="bg-success text-success-foreground">$0</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <Dialog open={showPasswordDialog} onOpenChange={setShowPasswordDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
            <DialogDescription>
              Enter your current password and choose a new one
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="currentPassword">Current Password</Label>
              <Input
                id="currentPassword"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="newPassword">New Password</Label>
              <Input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm New Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPasswordDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleChangePassword}>Change Password</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showEmailDialog} onOpenChange={setShowEmailDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Email Address</DialogTitle>
            <DialogDescription>
              Enter your password and new email address
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="passwordForEmail">Current Password</Label>
              <Input
                id="passwordForEmail"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="newEmailInput">New Email Address</Label>
              <Input
                id="newEmailInput"
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEmailDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleChangeEmail}>Change Email</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete your account
              and remove all your data from our servers.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteAccount}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Account
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Project Dialog */}
      <Dialog open={showProjectDialog} onOpenChange={setShowProjectDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{currentProject.id ? 'Edit Project' : 'Add New Project'}</DialogTitle>
            <DialogDescription>
              Add details about your project to help the AI understand your experience.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="projectTitle">Project Title *</Label>
              <Input
                id="projectTitle"
                placeholder="e.g., EcoTrack - Carbon Footprint Tracker"
                value={currentProject.title || ''}
                onChange={(e) => setCurrentProject(prev => ({ ...prev, title: e.target.value }))}
                maxLength={100}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="projectRole">Your Role</Label>
              <Input
                id="projectRole"
                placeholder="e.g., Lead Developer, UI/UX Designer"
                value={currentProject.role || ''}
                onChange={(e) => setCurrentProject(prev => ({ ...prev, role: e.target.value }))}
                maxLength={50}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="projectDescription">Description *</Label>
              <textarea
                id="projectDescription"
                className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Describe what the project does, the problem it solves, and your contributions..."
                value={currentProject.description || ''}
                onChange={(e) => setCurrentProject(prev => ({ ...prev, description: e.target.value }))}
                maxLength={500}
              />
              <p className="text-xs text-muted-foreground text-right">
                {(currentProject.description?.length || 0)}/500
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="projectTech">Tech Stack (comma-separated)</Label>
              <Input
                id="projectTech"
                placeholder="e.g., React, Python, Firebase, TensorFlow"
                value={techStackInput}
                onChange={(e) => setTechStackInput(e.target.value)}
                maxLength={200}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="projectUrl">Project URL</Label>
              <Input
                id="projectUrl"
                type="url"
                placeholder="https://github.com/yourname/project"
                value={currentProject.url || ''}
                onChange={(e) => setCurrentProject(prev => ({ ...prev, url: e.target.value }))}
                maxLength={200}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowProjectDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => {
              if (!currentProject.title?.trim() || !currentProject.description?.trim()) {
                toast({
                  title: 'Missing required fields',
                  description: 'Please provide a title and description.',
                  variant: 'destructive',
                });
                return;
              }
              
              const techStack = techStackInput
                .split(',')
                .map(s => s.trim())
                .filter(s => s.length > 0);
              
              const projectToSave: Project = {
                id: currentProject.id || crypto.randomUUID(),
                title: currentProject.title.trim(),
                description: currentProject.description.trim(),
                techStack,
                role: currentProject.role?.trim(),
                url: currentProject.url?.trim(),
              };
              
              setProfile(prev => {
                if (!prev) return null;
                const existingProjects = prev.projects || [];
                if (currentProject.id) {
                  return {
                    ...prev,
                    projects: existingProjects.map(p => p.id === currentProject.id ? projectToSave : p)
                  };
                }
                return {
                  ...prev,
                  projects: [...existingProjects, projectToSave]
                };
              });
              
              setShowProjectDialog(false);
              setCurrentProject({});
              setTechStackInput('');
              
              toast({
                title: currentProject.id ? 'Project updated' : 'Project added',
                description: 'Your project has been saved.',
              });
            }}>
              {currentProject.id ? 'Save Changes' : 'Add Project'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Experience Dialog */}
      <Dialog open={showExperienceDialog} onOpenChange={setShowExperienceDialog}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{currentExperience.id ? 'Edit Experience' : 'Add New Experience'}</DialogTitle>
            <DialogDescription>
              Add work experience, internships, or volunteer roles.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="expRole">Role / Position *</Label>
              <Input
                id="expRole"
                placeholder="e.g., Software Engineering Intern"
                value={currentExperience.role || ''}
                onChange={(e) => setCurrentExperience(prev => ({ ...prev, role: e.target.value }))}
                maxLength={100}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="expCompany">Company / Organization *</Label>
              <Input
                id="expCompany"
                placeholder="e.g., Google, Local NGO"
                value={currentExperience.company || ''}
                onChange={(e) => setCurrentExperience(prev => ({ ...prev, company: e.target.value }))}
                maxLength={100}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="expStartDate">Start Date *</Label>
                <Input
                  id="expStartDate"
                  type="month"
                  value={currentExperience.startDate || ''}
                  onChange={(e) => setCurrentExperience(prev => ({ ...prev, startDate: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="expEndDate">End Date</Label>
                <Input
                  id="expEndDate"
                  type="month"
                  value={currentExperience.endDate || ''}
                  onChange={(e) => setCurrentExperience(prev => ({ ...prev, endDate: e.target.value }))}
                  disabled={currentExperience.current}
                />
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Switch
                id="expCurrent"
                checked={currentExperience.current || false}
                onCheckedChange={(checked) => setCurrentExperience(prev => ({ 
                  ...prev, 
                  current: checked,
                  endDate: checked ? undefined : prev.endDate 
                }))}
              />
              <Label htmlFor="expCurrent">I currently work here</Label>
            </div>
            <div className="space-y-2">
              <Label htmlFor="expDescription">Description *</Label>
              <textarea
                id="expDescription"
                className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Describe your responsibilities, achievements, and skills used..."
                value={currentExperience.description || ''}
                onChange={(e) => setCurrentExperience(prev => ({ ...prev, description: e.target.value }))}
                maxLength={500}
              />
              <p className="text-xs text-muted-foreground text-right">
                {(currentExperience.description?.length || 0)}/500
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowExperienceDialog(false)}>
              Cancel
            </Button>
            <Button onClick={() => {
              if (!currentExperience.role?.trim() || !currentExperience.company?.trim() || !currentExperience.startDate || !currentExperience.description?.trim()) {
                toast({
                  title: 'Missing required fields',
                  description: 'Please fill in all required fields.',
                  variant: 'destructive',
                });
                return;
              }
              
              const experienceToSave: WorkExperience = {
                id: currentExperience.id || crypto.randomUUID(),
                role: currentExperience.role.trim(),
                company: currentExperience.company.trim(),
                startDate: currentExperience.startDate,
                endDate: currentExperience.endDate,
                description: currentExperience.description.trim(),
                current: currentExperience.current || false,
              };
              
              setProfile(prev => {
                if (!prev) return null;
                const existingExperience = prev.experience || [];
                if (currentExperience.id) {
                  return {
                    ...prev,
                    experience: existingExperience.map(e => e.id === currentExperience.id ? experienceToSave : e)
                  };
                }
                return {
                  ...prev,
                  experience: [...existingExperience, experienceToSave]
                };
              });
              
              setShowExperienceDialog(false);
              setCurrentExperience({});
              
              toast({
                title: currentExperience.id ? 'Experience updated' : 'Experience added',
                description: 'Your experience has been saved.',
              });
            }}>
              {currentExperience.id ? 'Save Changes' : 'Add Experience'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
