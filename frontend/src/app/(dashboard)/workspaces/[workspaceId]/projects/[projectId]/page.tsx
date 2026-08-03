"use client";

import { use } from "react";
import { useProject } from "@/features/projects/api/queries";
import { useVendors } from "@/features/vendors/api/queries";
import { useQuotations } from "@/features/quotations/api/queries";
import { ProjectSummaryCard } from "@/features/projects/components/ProjectSummaryCard";
import { AIReadinessPanel } from "@/features/projects/components/AIReadinessPanel";
import { ActivityTimeline } from "@/features/projects/components/ActivityTimeline";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";

export default function ProjectOverviewPage({ params }: { params: Promise<{ workspaceId: string; projectId: string }> }) {
  const resolvedParams = use(params);
  
  const { data: project, isLoading: projectLoading } = useProject(resolvedParams.workspaceId, resolvedParams.projectId);
  const { data: vendors, isLoading: vendorsLoading } = useVendors(resolvedParams.workspaceId, undefined, 1, 100);
  const { data: quotations, isLoading: quotationsLoading } = useQuotations(resolvedParams.workspaceId, resolvedParams.projectId, 1, 100);

  const isLoading = projectLoading || vendorsLoading || quotationsLoading;

  if (isLoading) {
    return (
      <div className="flex h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!project) return null;

  const vendorCount = vendors?.total || 0;
  const quotationCount = quotations?.total || 0;
  
  const hasVendors = vendorCount > 0;
  const hasQuotations = quotationCount > 0;
  const allQuotationsUploaded = hasQuotations && quotations!.items.every(q => !!q.file_name);

  // Artificial timeline derivation for Sprint 2 visualization mapping
  const events = [];
  if (project) {
    events.push({
      id: "ev_1",
      type: "project_created" as const,
      title: "Project Initialized",
      date: new Date(project.created_at).toLocaleString(),
      isLatest: !hasVendors
    });
  }
  if (hasVendors) {
    events.unshift({
      id: "ev_2",
      type: "vendor_added" as const,
      title: `${vendorCount} Vendor${vendorCount > 1 ? 's' : ''} Integrated`,
      date: new Date().toLocaleString(),
      isLatest: !hasQuotations
    });
  }
  if (hasQuotations) {
    events.unshift({
      id: "ev_3",
      type: "quotation_uploaded" as const,
      title: `${quotationCount} Document${quotationCount > 1 ? 's' : ''} Cached`,
      date: new Date().toLocaleString(),
      isLatest: true
    });
  }

  const triggerAnalysis = () => {
    toast.success("AI Analysis trigger has been queued for execution! Moving to Sprint 3 orchestration processing.");
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in zoom-in-95 duration-500 pb-8">
      {/* Left Column - Metrics */}
      <div className="md:col-span-2 flex flex-col gap-6">
        <ProjectSummaryCard 
          project={project} 
          vendorCount={vendorCount} 
          quotationCount={quotationCount} 
        />
        <ActivityTimeline events={events} />
      </div>

      {/* Right Column - AI Interaction */}
      <div className="flex flex-col gap-6">
        <AIReadinessPanel 
          hasVendors={hasVendors}
          hasQuotations={hasQuotations}
          allQuotationsUploaded={allQuotationsUploaded}
          onAnalyze={triggerAnalysis}
        />
        
        {/* Additional minimal storage hint */}
        <div className="rounded-lg border p-4 text-center bg-secondary/10">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Vault Storage</p>
          <p className="text-2xl font-bold font-mono text-primary/80">{(quotationCount * 1.4).toFixed(1)} <span className="text-sm font-sans">MB</span></p>
        </div>
      </div>
    </div>
  );
}
