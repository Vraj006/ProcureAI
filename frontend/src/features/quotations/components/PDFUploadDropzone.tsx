"use client";

import { useState, useCallback } from "react";
import { QuotationResponse } from "@/services/api/types";
import { useUploadPDF } from "@/features/quotations/api/queries";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { FileDown, FileUp, Loader2, CheckCircle2, AlertCircle, X, FileText } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface PDFUploadDropzoneProps {
  workspaceId: string;
  projectId: string;
  quotation: QuotationResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function PDFUploadDropzone({ workspaceId, projectId, quotation, open, onOpenChange }: PDFUploadDropzoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<"IDLE" | "UPLOADING" | "SUCCESS" | "ERROR">("IDLE");
  const [errorMessage, setErrorMessage] = useState("");

  const { mutateAsync: uploadPDF } = useUploadPDF();

  const resetState = () => {
    setFile(null);
    setProgress(0);
    setStatus("IDLE");
    setErrorMessage("");
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const validateAndSetFile = (selectedFile: File) => {
    if (selectedFile.type !== "application/pdf") {
      setStatus("ERROR");
      setErrorMessage("Only PDF files are allowed.");
      return;
    }
    if (selectedFile.size > 20 * 1024 * 1024) { // 20MB limit
      setStatus("ERROR");
      setErrorMessage("File exceeds 20MB limit.");
      return;
    }
    setFile(selectedFile);
    setStatus("IDLE");
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file || !quotation) return;

    setStatus("UPLOADING");
    try {
      await uploadPDF({
        workspaceId,
        projectId,
        quotationId: quotation.id,
        file,
        onProgress: (progressEvent: any) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setProgress(percentCompleted);
        }
      });
      setStatus("SUCCESS");
      setTimeout(() => {
        onOpenChange(false);
        resetState();
      }, 1500); // Visually linger on success for 1.5s
    } catch (error: any) {
      setStatus("ERROR");
      setErrorMessage(error.response?.data?.detail || "Failed to upload file");
    }
  };

  return (
    <Dialog open={open} onOpenChange={(op) => {
      onOpenChange(op);
      if (!op) resetState();
    }}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Upload Quotation PDF</DialogTitle>
          <DialogDescription>
            {quotation ? `Uploading document for ${quotation.quotation_number}` : ""}
          </DialogDescription>
        </DialogHeader>

        {status === "SUCCESS" ? (
          <div className="flex flex-col items-center justify-center p-8 text-center space-y-4 animate-in fade-in zoom-in duration-300">
            <div className="h-16 w-16 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="h-8 w-8" />
            </div>
            <div className="space-y-1">
              <h3 className="font-medium text-lg">Upload Complete</h3>
              <p className="text-sm text-muted-foreground">{file?.name}</p>
            </div>
          </div>
        ) : (
          <div className="space-y-4 pt-4 w-full min-w-0 overflow-hidden">
            
            {status === "ERROR" && (
              <div className="bg-destructive/10 text-destructive text-sm px-4 py-3 rounded-md flex items-start gap-2">
                <AlertCircle className="h-4 w-4 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium">Upload failed</p>
                  <p className="text-xs opacity-90">{errorMessage}</p>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6 -mr-2 -mt-1 text-destructive hover:bg-destructive/20" onClick={() => setStatus("IDLE")}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}

            {!file ? (
              <div
                className={cn(
                  "relative group flex flex-col items-center justify-center p-10 border-2 border-dashed rounded-lg transition-colors cursor-pointer",
                  dragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50 hover:bg-secondary/50",
                  status === "UPLOADING" && "opacity-50 pointer-events-none"
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  accept=".pdf,application/pdf"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  onChange={handleChange}
                  disabled={status === "UPLOADING"}
                />
                <div className="flex flex-col items-center justify-center text-muted-foreground group-hover:text-foreground transition-colors">
                  <FileUp className={cn("h-10 w-10 mb-4", dragActive && "text-primary")} />
                  <p className="text-sm font-medium mb-1">
                    Drag and drop your PDF here
                  </p>
                  <p className="text-xs">
                    or click to browse from directory
                  </p>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-4 p-4 border rounded-lg bg-secondary/20 w-full overflow-hidden">
                <div className="h-10 w-10 shrink-0 bg-blue-100 text-blue-600 rounded flex items-center justify-center">
                  <FileText className="h-5 w-5" />
                </div>
                <div className="flex-1 min-w-0 overflow-hidden">
                  <p className="text-sm font-medium truncate block w-full" title={file.name}>{file.name}</p>
                  <p className="text-xs text-muted-foreground">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
                {status !== "UPLOADING" && (
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-destructive shrink-0" onClick={resetState}>
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
            )}

            {status === "UPLOADING" && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-medium">
                  <span className="text-muted-foreground flex items-center gap-2">
                    <Loader2 className="h-3 w-3 animate-spin" /> Uploading securely...
                  </span>
                  <span>{progress}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>
            )}

            {file && status !== "UPLOADING" && (
              <Button className="w-full" onClick={handleUpload}>
                Start Upload
              </Button>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
