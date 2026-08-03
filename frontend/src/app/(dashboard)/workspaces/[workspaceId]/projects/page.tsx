"use client";

import { useProjects } from "@/features/projects/api/queries";
import { useWorkspace } from "@/features/workspaces/api/queries";
import { PageHeader } from "@/components/common/page-header";
import { ProjectCard } from "@/features/projects/components/ProjectCard";
import { CreateProjectDialog } from "@/features/projects/components/CreateProjectDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Plus, Search, Package, Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useState, use, useEffect } from "react";
import { ProjectResponse } from "@/services/api/types";

export default function WorkspaceProjectsPage({ params }: { params: Promise<{ workspaceId: string }> }) {
  // unwrap params for Next 15
  const unwrappedParams = use(params);
  const workspaceId = unwrappedParams.workspaceId;

  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  
  // Custom simple debouncer
  const [debouncedSearch, setDebouncedSearch] = useState("");
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
    }, 500);
    return () => clearTimeout(handler);
  }, [search]);
  
  const { data: workspace } = useWorkspace(workspaceId);
  const { data: projects, isLoading } = useProjects(workspaceId, debouncedSearch || undefined, 1, 50);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <Link href="/workspaces" className="flex flex-row items-center hover:text-foreground transition-colors">
          <ArrowLeft className="h-4 w-4 mr-1" />
          All Workspaces
        </Link>
        <span>/</span>
        <span className="font-medium text-foreground">{workspace?.name || "Workspace"}</span>
      </div>

      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <PageHeader 
          title="Projects" 
          description={`Showing active projects for ${workspace?.name || "this workspace"}.`} 
        />
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Project
        </Button>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-2">
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            type="search" 
            placeholder="Search projects..." 
            className="pl-9 bg-background" 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : !projects || projects.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 py-24 text-center border rounded-lg border-dashed bg-secondary/20">
          <Package className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
          <h3 className="text-xl font-medium tracking-tight mb-2">No Projects Found</h3>
          <p className="text-muted-foreground max-w-sm mb-6">
            {search ? "No projects matched your search criteria." : "Get started by creating your first procurement project."}
          </p>
          {!search && (
            <Button size="lg" onClick={() => setCreateOpen(true)}>Create Project</Button>
          )}
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {projects.items.map((project: ProjectResponse) => (
            <ProjectCard 
              key={project.id} 
              id={project.id}
              workspaceId={workspaceId}
              title={project.name}
              status={project.status as any}
              fileCount={0}
              timestamp={new Date(project.updated_at).toLocaleDateString()}
            />
          ))}
        </div>
      )}

      <CreateProjectDialog workspaceId={workspaceId} open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
