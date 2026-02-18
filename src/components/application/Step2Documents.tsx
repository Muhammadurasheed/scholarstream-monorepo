import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Upload, FileText, Check, X, Loader2 } from 'lucide-react';
import { apiService } from '@/services/api';
import { toast } from 'sonner';
import type { DocumentData, Scholarship } from '@/types/scholarship';

interface Step2DocumentsProps {
  data: DocumentData[];
  scholarship: Scholarship;
  onChange: (data: DocumentData[]) => void;
  onNext: () => void;
  onPrevious: () => void;
  onSave: () => void;
  userId: string;
  scholarshipId: string;
}

export default function Step2Documents({
  data,
  scholarship,
  onChange,
  onNext,
  onPrevious,
  onSave,
  userId,
  scholarshipId,
}: Step2DocumentsProps) {
  const [uploading, setUploading] = useState<string | null>(null);

  const requiredDocuments = [];
  if (scholarship.requirements.transcript) requiredDocuments.push({ type: 'transcript', name: 'Transcript', required: true });
  if (scholarship.requirements.resume) requiredDocuments.push({ type: 'resume', name: 'Resume/CV', required: true });
  requiredDocuments.push({ type: 'fafsa', name: 'FAFSA (if applicable)', required: false });

  const handleFileUpload = async (file: File, documentType: string) => {
    try {
      setUploading(documentType);

      const response = await apiService.uploadDocument(file, userId, scholarshipId, documentType);

      onChange([...data.filter(d => d.document_type !== documentType), response.document]);
      toast.success('Document uploaded successfully');
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error('Failed to upload document');
    } finally {
      setUploading(null);
    }
  };

  const handleRemove = (documentType: string) => {
    onChange(data.filter(d => d.document_type !== documentType));
    toast.success('Document removed');
  };

  const getDocument = (type: string) => data.find(d => d.document_type === type);

  const canContinue = requiredDocuments
    .filter(d => d.required)
    .every(d => getDocument(d.type));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground mb-2">Upload Required Documents</h1>
        <p className="text-muted-foreground">Make sure all files are clear and legible (PDF preferred)</p>
      </div>

      <Card className="bg-blue-500/10 border-blue-500/20">
        <CardContent className="pt-6">
          <h3 className="font-semibold text-foreground mb-2">Document Requirements:</h3>
          <ul className="space-y-1 text-sm text-muted-foreground">
            <li>✓ Clear and legible (not blurry)</li>
            <li>✓ All pages included</li>
            <li>✓ File size under 10MB</li>
            <li>✓ PDF format preferred</li>
          </ul>
        </CardContent>
      </Card>

      {/* Document Upload Cards */}
      <div className="space-y-4">
        {requiredDocuments.map((doc) => {
          const uploadedDoc = getDocument(doc.type);
          const isUploading = uploading === doc.type;

          return (
            <Card key={doc.type}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{doc.name}</CardTitle>
                    <CardDescription>
                      {doc.required ? (
                        <span className="text-destructive font-medium">Required</span>
                      ) : (
                        <span className="text-muted-foreground">Optional</span>
                      )}
                    </CardDescription>
                  </div>
                  {uploadedDoc && (
                    <div className="flex items-center gap-2 text-green-600">
                      <Check className="h-5 w-5" />
                      <span className="text-sm font-medium">Uploaded</span>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {uploadedDoc ? (
                  <div className="flex items-center justify-between p-4 bg-muted rounded-lg">
                    <div className="flex items-center gap-3">
                      <FileText className="h-8 w-8 text-blue-500" />
                      <div>
                        <p className="font-medium text-foreground">{uploadedDoc.file_name}</p>
                        <p className="text-sm text-muted-foreground">
                          {uploadedDoc.file_size ? `${(uploadedDoc.file_size / 1024).toFixed(0)} KB` : 'Uploaded'}
                        </p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => window.open(uploadedDoc.file_url, '_blank')}
                      >
                        View
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRemove(doc.type)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ) : (
                  <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors">
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={(e) => {
                        const file = e.target.files?.[0];
                        if (file) {
                          if (file.size > 10 * 1024 * 1024) {
                            toast.error('File too large. Maximum size is 10MB.');
                            return;
                          }
                          handleFileUpload(file, doc.type);
                        }
                      }}
                      disabled={isUploading}
                    />
                    {isUploading ? (
                      <div className="flex flex-col items-center gap-2">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        <p className="text-sm text-muted-foreground">Uploading...</p>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center gap-2">
                        <Upload className="h-8 w-8 text-muted-foreground" />
                        <p className="text-sm text-muted-foreground">
                          Click to upload or drag and drop
                        </p>
                        <p className="text-xs text-muted-foreground">PDF, JPG, PNG (max 10MB)</p>
                      </div>
                    )}
                  </label>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-6">
        <div className="space-x-2">
          <Button variant="outline" onClick={onPrevious}>
            Previous
          </Button>
          <Button variant="ghost" onClick={onSave}>
            Save Draft
          </Button>
        </div>
        <Button onClick={onNext} size="lg" disabled={!canContinue}>
          Continue
        </Button>
      </div>
    </div>
  );
}
