import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BrainCircuit, CheckCircle2 } from "lucide-react";
import { ProjectResponse } from "@/services/api/types";
import { cn } from "@/lib/utils";

const progressMap: Record<string, { percent: number; label: string; done: boolean }> = {
  DRAFT: { percent: 0, label: "Awaiting Quotations", done: false },
  PROCESSING: { percent: 40, label: "Evaluating compliance & structure...", done: false },
  HUMAN_REVIEW_REQUIRED: { percent: 90, label: "Awaiting Human Decision", done: false },
  COMPLETED: { percent: 100, label: "Orchestration Complete", done: true },
  REJECTED: { percent: 100, label: "Rejected by Reviewer", done: true },
};

export function AnalysisProgressCard({ project }: { project?: ProjectResponse }) {
  if (!project) return null;
  const statusInfo = progressMap[project.status] || { percent: 0, label: "Unknown status", done: false };

  return (
    <Card className="shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">Analysis Summary</CardTitle>
        <Badge 
          variant="outline" 
          className={cn(
            statusInfo.done ? "bg-emerald-500/10 text-emerald-600 border-emerald-200" : "bg-blue-500/10 text-blue-600 border-blue-200"
          )}
        >
          {statusInfo.done && <CheckCircle2 className="w-3 h-3 mr-1" />}
          {statusInfo.percent}% Complete
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-4 pt-2">
          
          <div className="flex items-center gap-4">
            <div className="h-10 w-10 shrink-0 rounded-full bg-primary/10 flex items-center justify-center text-primary">
              <BrainCircuit className={cn("h-5 w-5", !statusInfo.done && project.status !== "DRAFT" && "animate-pulse")} />
            </div>
            <div className="space-y-1">
              <p className="font-medium text-sm">ProcureAI Engine</p>
              <p className="text-xs text-muted-foreground">{statusInfo.label}</p>
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-medium">
              <span>Overall Progress</span>
              <span>{statusInfo.percent}%</span>
            </div>
            <div className="h-2 w-full bg-secondary rounded-full overflow-hidden">
              <div className="h-full bg-primary transition-all duration-500" style={{ width: `${statusInfo.percent}%` }} />
            </div>
          </div>
          
        </div>
      </CardContent>
    </Card>
  );
}
