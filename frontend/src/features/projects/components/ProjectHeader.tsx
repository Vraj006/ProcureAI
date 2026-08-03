"use client";

import { useProject } from "@/features/projects/api/queries";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const statusConfig: Record<string, { label: string; color: string }> = {
  DRAFT: { label: "Draft", color: "bg-slate-100 text-slate-700" },
  PROCESSING: { label: "Processing AI", color: "bg-blue-100 text-blue-700" },
  HUMAN_REVIEW_REQUIRED: { label: "Review Required", color: "bg-amber-100 text-amber-700" },
  COMPLETED: { label: "Completed", color: "bg-emerald-100 text-emerald-700" },
  REJECTED: { label: "Rejected", color: "bg-red-100 text-red-700" },
};

export function ProjectHeader({ workspaceId, projectId }: { workspaceId: string; projectId: string }) {
  const { data: project, isLoading } = useProject(workspaceId, projectId);

  if (isLoading) {
    return <div className="h-20 flex items-center"><Loader2 className="w-5 h-5 animate-spin text-muted-foreground" /></div>;
  }

  if (!project) return null;

  const currentStatus = statusConfig[project.status] || { label: project.status, color: "bg-slate-100 text-slate-700" };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <Link href={`/workspaces/${workspaceId}/projects`} className="flex flex-row items-center hover:text-foreground transition-colors">
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to Projects
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-foreground">{project.name}</h1>
          <p className="text-sm text-muted-foreground">ID: {project.id}</p>
        </div>
        <Badge variant="secondary" className={cn("px-3 py-1 text-sm rounded-sm", currentStatus.color)}>
          {currentStatus.label}
        </Badge>
      </div>
    </div>
  );
}
