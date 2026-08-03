"use client";

import { useWorkflowStatus, useStartAnalysis } from "../hooks/useAnalysisQueries";
import { WorkflowTimeline } from "./WorkflowTimeline";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { AlertCircle, BrainCircuit, Play, Sparkles } from "lucide-react";

interface AnalysisDashboardProps {
  workspaceId: string;
  projectId: string;
}

export function AnalysisDashboard({ workspaceId, projectId }: AnalysisDashboardProps) {
  const { data: statusData, isLoading, error } = useWorkflowStatus(workspaceId, projectId);
  const { mutateAsync: startAnalysis, isPending: isAnalyzing } = useStartAnalysis(workspaceId, projectId);

  const handleStartAnalysis = async () => {
    toast.promise(startAnalysis(), {
      loading: "Triggering ProcureAI Orchestrator. The LangGraph workflows are running...",
      success: "Analysis successfully completed!",
      error: (err) => `Analysis failed: ${err.response?.data?.detail || err.message}`,
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[400px] w-full rounded-xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="relative w-full rounded-lg border border-destructive/50 p-4 [&>svg]:absolute [&>svg]:text-destructive [&>svg]:left-4 [&>svg]:top-4 [&>svg+div]:translate-y-[-3px] [&:has(svg)]:pl-11 text-destructive">
        <AlertCircle className="h-4 w-4" />
        <h5 className="mb-1 font-medium leading-none tracking-tight">Error loading analysis state</h5>
        <div className="text-sm [&_p]:leading-relaxed">
          {error.message || "Failed to load workflow state. Please try again."}
        </div>
      </div>
    );
  }

  const steps = [
    {
      id: "doc_proc",
      label: "Document Processing",
      status: statusData?.steps?.document_processing || "pending",
      description: "Parsing PDFs to extract raw tabular texts.",
    },
    {
      id: "extraction",
      label: "Information Extraction",
      status: statusData?.steps?.extraction || "pending",
      description: "Utilizing LLM agents to extract commercial terms and line items.",
    },
    {
      id: "comparison",
      label: "Vendor Comparison",
      status: statusData?.steps?.comparison || "pending",
      description: "Matrix comparison algorithm calculating rankings.",
    },
    {
      id: "compliance",
      label: "Compliance Validation",
      status: statusData?.steps?.compliance || "pending",
      description: "Checking constraints against company policies.",
    },
    {
      id: "recommendation",
      label: "Strategic Recommendation",
      status: statusData?.steps?.recommendation || "pending",
      description: "LangGraph finalizing the final selection reasoning.",
    },
    {
      id: "human_review",
      label: "Human Review",
      status: statusData?.steps?.human_review || "pending",
      description: "User input loop for Approval/Rejection of the AI's selection.",
    },
  ] as any[];

  const isCompleted = statusData?.status === "completed";

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <BrainCircuit className="h-6 w-6 text-primary" />
            AI Analysis Dashboard
          </h2>
          <p className="text-muted-foreground mt-1 text-sm">
            Monitor the multi-agent LangGraph orchestration across your vendor quotations.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={isCompleted ? "default" : "secondary"} className="text-sm px-3 py-1">
            {isCompleted ? "Analysis Complete" : "Pending Analysis"}
          </Badge>
          <Button 
            onClick={handleStartAnalysis} 
            disabled={isAnalyzing || statusData?.status === "completed"}
            className="gap-2"
          >
            {isAnalyzing ? (
              <Sparkles className="h-4 w-4 animate-pulse" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {isAnalyzing ? "Processing..." : "Analyze Procurement"}
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Workflow Orchestration Timeline</CardTitle>
          <CardDescription>
            The execution DAG tracking the Document, Extractor, Comparison, Compliance, and Recommendation Agents.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <WorkflowTimeline 
            steps={steps}
            isGlobalLoading={isAnalyzing}
          />
        </CardContent>
      </Card>
    </div>
  );
}
