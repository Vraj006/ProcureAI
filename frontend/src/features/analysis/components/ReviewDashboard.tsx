"use client";

import { useState } from "react";
import { useRecommendation, useSubmitReview, useWorkflowStatus } from "../hooks/useAnalysisQueries";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { CheckCircle2, FileWarning, Target, XCircle, ArrowRight, Loader2, Bot, RefreshCw } from "lucide-react";
import { motion } from "framer-motion";
import { ReviewSubmitPayload } from "@/services/api/analysis";

interface ReviewDashboardProps {
  workspaceId: string;
  projectId: string;
}

export function ReviewDashboard({ workspaceId, projectId }: ReviewDashboardProps) {
  const { data: wfStatus, isLoading } = useWorkflowStatus(workspaceId, projectId);
  const submitReview = useSubmitReview(workspaceId, projectId);

  const [comments, setComments] = useState("");
  
  if (isLoading) {
    return (
      <div className="flex justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const status = wfStatus?.steps?.human_review;
  const isWorkflowCompleted = wfStatus?.status === "completed";
  const isPendingReview = status === "pending" && isWorkflowCompleted;
  
  const handleSubmission = async (decision: ReviewSubmitPayload["status"]) => {
    if ((decision === "rejected" || decision === "requires_changes") && !comments.trim()) {
      toast.error("Comments are required for revisions or rejections.");
      return;
    }
    
    toast.promise(submitReview.mutateAsync({ status: decision, comments }), {
      loading: "Submitting review...",
      success: `Decision submitted successfully. ${decision === "requires_changes" ? "LangGraph will now route back to recommendations." : ""}`,
      error: (err) => `Submission failed: ${err.message}`
    });
  };

  if (!isPendingReview && status !== "requires_changes" && status !== "rejected" && status !== "approved") {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed bg-secondary/10 shadow-sm mt-4">
        <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mb-6">
          <Bot className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-xl font-bold tracking-tight mb-2">Review Pending AI Completion</h3>
        <p className="text-muted-foreground max-w-sm text-sm">
          Please wait for the AI agents to complete Document Processing, Extraction, Comparison, Compliance, and Recommendation generation before instituting Human-in-the-Loop review constraints.
        </p>
      </div>
    );
  }

  const isLocked = status === "approved" || submitReview.isPending;

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div className="flex items-center gap-2 mb-2">
        <Target className="h-6 w-6 text-primary" />
        <h2 className="text-2xl font-bold tracking-tight">Manual Human-in-the-Loop Review</h2>
      </div>

      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
        <Card className={isLocked ? "bg-muted/30 border-muted" : "border-primary/20 shadow-md"}>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-xl">Executive Review Required</CardTitle>
                <CardDescription className="mt-1.5">
                  Approve the AI recommendation to finalize this procurement cycle, or request changes to trigger LangGraph reprocessing.
                </CardDescription>
              </div>
              {status === "approved" && (
                <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">
                  <CheckCircle2 className="w-3 h-3 mr-1" /> Approved
                </Badge>
              )}
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Review Comments & Justification</label>
              <Textarea 
                placeholder="Enter any negotiation insights, strict overrides, or reasoning for rejection here to fine-tune the AI rerun."
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                disabled={isLocked}
                className="min-h-[120px] resize-none"
              />
              <p className="text-xs text-muted-foreground">Required if rejecting or requesting changes.</p>
            </div>
          </CardContent>

          <CardFooter className="bg-muted/20 border-t py-4 px-6 flex justify-between items-center rounded-b-xl">
            {isLocked ? (
              <p className="text-sm text-emerald-600 font-medium flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" /> This procurement cycle has been successfully concluded.
              </p>
            ) : (
              <>
                <Button 
                  variant="outline" 
                  className="text-amber-600 border-amber-200 hover:bg-amber-50 hover:text-amber-700"
                  onClick={() => handleSubmission("requires_changes")}
                  disabled={submitReview.isPending}
                >
                  <RefreshCw className="mr-2 h-4 w-4" /> Loop Back (Require Changes)
                </Button>
                
                <div className="flex gap-3">
                  <Button 
                    variant="destructive" 
                    onClick={() => handleSubmission("rejected")}
                    disabled={submitReview.isPending}
                  >
                    <XCircle className="mr-2 h-4 w-4" /> Reject Entirely
                  </Button>
                  
                  <Button 
                    onClick={() => handleSubmission("approved")}
                    disabled={submitReview.isPending}
                    className="bg-emerald-600 hover:bg-emerald-700"
                  >
                    <CheckCircle2 className="mr-2 h-4 w-4" /> Approve Recommendation
                  </Button>
                </div>
              </>
            )}
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  );
}
