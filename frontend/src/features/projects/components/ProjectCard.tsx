import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Clock, Users, ArrowRight } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface ProjectCardProps {
  id: string;
  workspaceId: string;
  title: string;
  status: string;
  fileCount: number;
  timestamp: string;
}

const statusConfig: Record<string, { label: string; color: string }> = {
  DRAFT: { label: "Draft", color: "bg-slate-100 text-slate-700" },
  PROCESSING: { label: "Processing AI", color: "bg-blue-100 text-blue-700" },
  HUMAN_REVIEW_REQUIRED: { label: "Review Required", color: "bg-amber-100 text-amber-700" },
  COMPLETED: { label: "Completed", color: "bg-emerald-100 text-emerald-700" },
  REJECTED: { label: "Rejected", color: "bg-red-100 text-red-700" },
};

export function ProjectCard({ id, workspaceId, title, status, fileCount, timestamp }: ProjectCardProps) {
  const currentStatus = statusConfig[status] || { label: status, color: "bg-slate-100 text-slate-700" };

  return (
    <Link href={`/workspaces/${workspaceId}/projects/${id}`}>
      <Card className="h-full cursor-pointer hover:border-primary/50 transition-colors shadow-sm group">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="space-y-1 pr-6">
              <h3 className="font-semibold text-lg line-clamp-1" title={title}>{title}</h3>
              <p className="text-xs text-muted-foreground truncate">{id}</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          
          <div className="flex items-center justify-between mb-4">
             <Badge variant="secondary" className={cn("rounded-sm", currentStatus.color)}>
              {currentStatus.label}
             </Badge>
          </div>

          <div className="flex items-center justify-between text-xs text-muted-foreground mt-6 pt-4 border-t border-dashed">
            <div className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              <span>{timestamp}</span>
            </div>
            <div className="flex items-center gap-1 text-primary group-hover:translate-x-1 transition-transform">
              <span>View details</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
