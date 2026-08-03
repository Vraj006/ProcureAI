import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Info, Calendar, AlignLeft, Hash } from "lucide-react";
import { ProjectResponse } from "@/services/api/types";

export function ProjectMetadataCard({ project }: { project: ProjectResponse }) {
  return (
    <Card className="shadow-sm">
      <CardHeader className="pb-3 border-b mb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Info className="w-5 h-5 text-muted-foreground" />
          Project Details
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4">
          <div className="grid grid-cols-3 gap-2 py-2 border-b border-dashed">
            <div className="text-sm text-muted-foreground flex items-center gap-2">
              <Hash className="w-4 h-4" /> ID
            </div>
            <div className="col-span-2 text-sm font-medium truncate" title={project.id}>
              {project.id}
            </div>
          </div>
          
          <div className="grid grid-cols-3 gap-2 py-2 border-b border-dashed">
            <div className="text-sm text-muted-foreground flex items-center gap-2">
              <Calendar className="w-4 h-4" /> Created
            </div>
            <div className="col-span-2 text-sm font-medium">
              {new Date(project.created_at).toLocaleDateString()}
            </div>
          </div>
          
          <div className="grid grid-cols-1 gap-2 py-2">
            <div className="text-sm text-muted-foreground flex items-center gap-2">
              <AlignLeft className="w-4 h-4" /> Description
            </div>
            <div className="text-sm leading-relaxed mt-1">
              {project.description || <span className="text-muted-foreground italic">No description provided.</span>}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
