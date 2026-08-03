import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Package, ChevronRight, Loader2 } from "lucide-react";
import Link from "next/link";
import { ProjectResponse } from "@/services/api/types";

export function RecentProjectsCard({ projects, workspaceId, isLoading }: { projects?: ProjectResponse[], workspaceId?: string, isLoading?: boolean }) {
  return (
    <Card className="col-span-1 md:col-span-2 lg:col-span-4 shadow-sm border-muted">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Recent Projects</CardTitle>
          <CardDescription>Latest active procurement cycles.</CardDescription>
        </div>
        {workspaceId && !isLoading && (
          <Link href={`/workspaces/${workspaceId}/projects`} className="text-sm font-medium text-primary flex items-center hover:underline">
            View all <ChevronRight className="w-4 h-4 ml-1" />
          </Link>
        )}
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex justify-center p-6"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
        ) : !projects || projects.length === 0 ? (
          <div className="text-center p-6 text-sm text-muted-foreground border rounded-lg border-dashed">
            No projects found in this workspace. 
            {workspaceId && (
               <div className="mt-2 text-primary font-medium">
                  <Link href={`/workspaces/${workspaceId}/projects/new`}>Create your first Procurement Project</Link>
               </div>
            )}
            {!workspaceId && (
               <div className="mt-2 text-primary font-medium">
                  <Link href={`/workspaces/`}>Create your first Workspace</Link>
               </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {projects.map((project) => (
              <Link href={`/workspaces/${workspaceId}/projects/${project.id}`} key={project.id} className="flex items-center justify-between p-3 rounded-lg border border-transparent hover:border-border hover:bg-secondary/20 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-md bg-primary/10 flex items-center justify-center text-primary">
                    <Package className="h-5 w-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium leading-none">{project.name}</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      {new Date(project.updated_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <Badge variant="outline">{project.status}</Badge>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
