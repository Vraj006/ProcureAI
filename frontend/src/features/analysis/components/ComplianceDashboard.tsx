"use client";

import { useCompliance } from "../hooks/useAnalysisQueries";
import { useVendors } from "@/features/vendors/api/queries";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle, ShieldCheck, FileWarning, ShieldAlert, ChevronDown, ChevronRight, XCircle, Info } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface ComplianceDashboardProps {
  workspaceId: string;
  projectId: string;
}

export function ComplianceDashboard({ workspaceId, projectId }: ComplianceDashboardProps) {
  const { data: complianceResponse, isLoading, error } = useCompliance(workspaceId, projectId);
  const { data: vendorsData } = useVendors(workspaceId, undefined, 1, 100);
  const [expandedVendorId, setExpandedVendorId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="space-y-4">
         <Skeleton className="h-[200px] w-full rounded-xl" />
         <Skeleton className="h-[200px] w-full rounded-xl" />
      </div>
    );
  }

  if (error || !complianceResponse?.success) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed bg-secondary/10 shadow-sm mt-4">
        <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mb-6">
          <FileWarning className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-xl font-bold tracking-tight mb-2">Compliance Scans Unavailable</h3>
        <p className="text-muted-foreground max-w-sm text-sm">
          {error?.message || complianceResponse?.errors?.[0] || "Policy analysis has not been executed yet. Please run AI analysis first."}
        </p>
      </div>
    );
  }

  const evaluations = complianceResponse.data?.quotation_results || [];

  const getStatusBadge = (status: string, totalIssues: number) => {
    if (status?.toLowerCase() === "compliant") {
      return <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-200 border-emerald-200"><ShieldCheck className="w-3 h-3 mr-1" /> Compliant</Badge>;
    }
    if (status?.toLowerCase() === "non_compliant" || status?.toLowerCase() === "non-compliant") {
      return <Badge className="bg-destructive/10 text-destructive hover:bg-destructive/20 border-destructive/20"><XCircle className="w-3 h-3 mr-1" /> Non-Compliant</Badge>;
    }
    return <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-200 border-amber-200"><AlertTriangle className="w-3 h-3 mr-1" /> Needs Attention</Badge>;
  };

  const getSeverityIcon = (sev: string) => {
    const s = sev?.toLowerCase();
    if (s === "error") return <ShieldAlert className="w-4 h-4 text-destructive" />;
    if (s === "warning") return <AlertTriangle className="w-4 h-4 text-amber-500" />;
    return <Info className="w-4 h-4 text-blue-500" />;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-2">
        <ShieldCheck className="h-6 w-6 text-primary" />
        <h2 className="text-2xl font-bold tracking-tight">Policy & Compliance Audit</h2>
      </div>

      <div className="space-y-4">
        {evaluations.map((evaluation: any, idx: number) => {
          const isExpanded = expandedVendorId === evaluation.quotation_id;
          const issues = evaluation.issues || [];
          const totalIssues = (evaluation.failed_checks || 0) + (evaluation.warning_count || 0);
          
          return (
            <Card key={idx} className={cn("transition-all duration-200 border", isExpanded ? "border-primary/50 shadow-md ring-1 ring-primary/20" : "")}>
              <div 
                className="p-6 flex items-center justify-between cursor-pointer"
                onClick={() => setExpandedVendorId(isExpanded ? null : evaluation.quotation_id)}
              >
                <div className="flex items-center gap-4">
                  <div className={cn("p-2 rounded-full", totalIssues > 0 ? "bg-amber-100 text-amber-600" : "bg-emerald-100 text-emerald-600")}>
                    {totalIssues > 0 ? <AlertTriangle className="h-5 w-5" /> : <ShieldCheck className="h-5 w-5" />}
                  </div>
                  <div>
                    <h3 className="font-bold text-lg">{evaluation.vendor_name || "Unknown Vendor"}</h3>
                    <p className="text-sm text-muted-foreground">
                      {totalIssues} compliance constraint violation{totalIssues !== 1 ? 's' : ''} detected
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-4">
                  {getStatusBadge(evaluation.status, totalIssues)}
                  <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0">
                    {isExpanded ? <ChevronDown className="h-5 w-5" /> : <ChevronRight className="h-5 w-5" />}
                  </Button>
                </div>
              </div>

              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="px-6 pb-6 pt-2 border-t bg-muted/20">
                      {issues.length === 0 ? (
                        <div className="text-sm text-muted-foreground py-4 flex items-center gap-2">
                          <ShieldCheck className="h-4 w-4 text-emerald-500" />
                          Vendor perfectly strictly adheres to all company guidelines. No issues generated during parsing.
                        </div>
                      ) : (
                        <ul className="space-y-3 mt-4">
                          {issues.map((issue: any, idx: number) => (
                            <li key={idx} className="flex gap-3 bg-background p-3 rounded-md border text-sm items-start shadow-sm">
                              <div className="mt-0.5">{getSeverityIcon(issue.severity)}</div>
                              <div className="flex-1">
                                <span className={cn(
                                  "font-semibold text-xs tracking-wide uppercase px-2 py-0.5 rounded-sm mb-1 inline-block",
                                  issue.severity?.toLowerCase() === "error" ? "bg-destructive/10 text-destructive" :
                                  issue.severity?.toLowerCase() === "warning" ? "bg-amber-100 text-amber-700" :
                                  "bg-blue-100 text-blue-700"
                                )}>
                                  {issue.severity || "Standard"} Issue
                                </span>
                                <p className="text-foreground leading-relaxed font-medium mt-1">
                                  <strong>{issue.check_name}</strong>: {issue.message}
                                </p>
                              </div>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>
          );
        })}
        {evaluations.length === 0 && (
          <div className="p-8 text-center text-muted-foreground bg-muted/20 rounded-lg border border-dashed">
            No compliance evaluations recorded.
          </div>
        )}
      </div>
    </div>
  );
}
