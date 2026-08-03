"use client";

import { useRecommendation, useWorkflowStatus } from "../hooks/useAnalysisQueries";
import { useVendors } from "@/features/vendors/api/queries";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { FileWarning, Info, Lightbulb, ThumbsUp, AlertTriangle, ListChecks, CheckCircle2 } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface RecommendationDashboardProps {
  workspaceId: string;
  projectId: string;
}

export function RecommendationDashboard({ workspaceId, projectId }: RecommendationDashboardProps) {
  const { data: recResponse, isLoading, error } = useRecommendation(workspaceId, projectId);
  const { data: wfStatus } = useWorkflowStatus(workspaceId, projectId);
  const { data: vendorsData } = useVendors(workspaceId, undefined, 1, 100);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-[200px] w-full rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Skeleton className="h-[300px] w-full rounded-xl" />
          <Skeleton className="h-[300px] w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (error || !recResponse?.success) {
    const isHumanRerun = wfStatus?.steps?.human_review === "rejected" || wfStatus?.steps?.human_review === "requires_changes";
    
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed bg-secondary/10 shadow-sm mt-4">
        <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mb-6">
          <FileWarning className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-xl font-bold tracking-tight mb-2">Recommendation Unavailable</h3>
        <p className="text-muted-foreground max-w-sm text-sm">
          {isHumanRerun 
            ? "Your reviewer requested changes. The system is re-generating a recommendation." 
            : (error?.message || recResponse?.errors?.[0] || "AI Orchestrator is pending consensus algorithms.")}
        </p>
      </div>
    );
  }

  const rec = recResponse.data;

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.15 }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0 }
  };

  const confidenceScore = rec.confidence_score || 0;
  const confidenceColor = 
    confidenceScore >= 80 ? "text-emerald-600 border-emerald-500/20 bg-emerald-500/10" :
    confidenceScore >= 60 ? "text-amber-600 border-amber-500/20 bg-amber-500/10" :
    "text-destructive border-destructive/20 bg-destructive/10";

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-2">
        <Lightbulb className="h-6 w-6 text-primary" />
        <h2 className="text-2xl font-bold tracking-tight">Executive Recommendation</h2>
      </div>

      <motion.div variants={container} initial="hidden" animate="show" className="space-y-6">
        
        {/* Top Recommendation Banner */}
        <motion.div variants={item}>
          <Card className="border-primary/30 shadow-md bg-gradient-to-br from-background to-primary/5 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8 opacity-5">
               <ThumbsUp className="w-48 h-48" />
            </div>
            <CardHeader className="pb-3 border-b border-primary/10">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-sm font-medium text-primary tracking-widest uppercase mb-2">
                     Optimal Selection
                  </CardTitle>
                  <div className="text-3xl font-bold tracking-tight mb-2">
                    {rec.recommended_vendor || "None Selected"}
                  </div>
                </div>
                <div className="text-center">
                  <div className={cn("inline-flex items-center justify-center p-4 rounded-full border-[3px]", confidenceColor)}>
                     <span className="text-2xl font-bold">{Math.round(confidenceScore)}</span>
                     <span className="text-sm ml-0.5 opacity-70">%</span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-2 font-medium tracking-wide uppercase">Confidence</div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="pt-6 relative z-10">
              <h4 className="font-semibold text-foreground flex items-center gap-2 mb-2">
                 <Info className="h-4 w-4 text-primary" /> Algorithmic Reasoning
              </h4>
              <p className="text-foreground/90 leading-relaxed text-sm">
                {rec.reasoning}
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div variants={item}>
            <Card className="h-full border-emerald-500/20 bg-gradient-to-b from-background to-emerald-50/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-emerald-700 flex items-center gap-2 text-base">
                  <CheckCircle2 className="h-5 w-5" /> Strengths
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {rec.strengths?.map((str: string, i: number) => (
                    <li key={i} className="flex gap-3 text-sm items-start">
                      <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                      <span className="leading-relaxed text-foreground/80">{str}</span>
                    </li>
                  ))}
                  {!rec.strengths?.length && <li className="text-sm text-muted-foreground">No strengths categorized.</li>}
                </ul>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={item}>
            <Card className="h-full border-amber-500/20 bg-gradient-to-b from-background to-amber-50/30">
              <CardHeader className="pb-3">
                <CardTitle className="text-amber-700 flex items-center gap-2 text-base">
                  <AlertTriangle className="h-5 w-5" /> Associated Risks
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {rec.risks?.map((risk: string, i: number) => (
                    <li key={i} className="flex gap-3 text-sm items-start">
                      <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                      <span className="leading-relaxed text-foreground/80">{risk}</span>
                    </li>
                  ))}
                  {!rec.risks?.length && <li className="text-sm text-muted-foreground text-emerald-600 font-medium">No major risks identified.</li>}
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {rec.alternatives && rec.alternatives.length > 0 && (
          <motion.div variants={item}>
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-base flex items-center gap-2">
                   <ListChecks className="w-5 h-5 text-muted-foreground" /> Viable Alternatives
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {rec.alternatives.map((alt: string, idx: number) => (
                  <div key={idx} className="flex flex-col md:flex-row md:items-center justify-between p-4 rounded-lg border bg-muted/20 gap-4">
                    <div>
                      <p className="text-sm text-muted-foreground mt-1 max-w-xl">{alt}</p>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        )}

      </motion.div>
    </div>
  );
}
