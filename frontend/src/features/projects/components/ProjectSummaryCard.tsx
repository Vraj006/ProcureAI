import { ProjectResponse } from "@/services/api/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Building, FileBox, CheckCircle2, UserCircle, Calendar, Hash } from "lucide-react";

export function ProjectSummaryCard({ project, vendorCount, quotationCount }: { project: ProjectResponse, vendorCount: number, quotationCount: number }) {
  return (
    <Card className="h-full">
      <CardHeader className="pb-4">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Hash className="h-4 w-4" /> Snapshot
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        
        <div className="flex flex-col gap-1">
          <h3 className="text-2xl font-bold tracking-tight text-primary">
            {project.name}
          </h3>
          <p className="text-sm text-muted-foreground">
            {project.description || "No description provided for this procurement project."}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-100 text-blue-600 rounded-lg">
              <Building className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold">{vendorCount}</p>
              <p className="text-xs text-muted-foreground">Registered Vendors</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-indigo-100 text-indigo-600 rounded-lg">
              <FileBox className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold">{quotationCount}</p>
              <p className="text-xs text-muted-foreground">Uploaded Documents</p>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-border pt-4 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
             <Calendar className="h-3.5 w-3.5" />
             Created on {new Date(project.created_at).toLocaleDateString()}
          </div>
          <Badge variant="outline" className="font-normal capitalize shadow-none">
            {project.status.toLowerCase()}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
