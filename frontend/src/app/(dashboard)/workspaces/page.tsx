"use client";

import { useWorkspaces } from "@/features/workspaces/api/queries";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { Plus, Factory, Loader2 } from "lucide-react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { CreateWorkspaceDialog } from "@/features/workspaces/components/CreateWorkspaceDialog";
import { useState } from "react";

export default function WorkspacesPage() {
  const { data: workspaces, isLoading } = useWorkspaces();
  const [createOpen, setCreateOpen] = useState(false);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <PageHeader 
          title="Workspaces" 
          description="Manage your organizational units and boundaries." 
        />
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Workspace
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : !workspaces || workspaces.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 py-24 text-center border rounded-lg border-dashed bg-secondary/10">
          <Factory className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
          <h3 className="text-xl font-medium tracking-tight mb-2">No Workspaces Found</h3>
          <p className="text-muted-foreground max-w-sm mb-6">
            Workspaces organize your procurement projects. Create your first workspace to get started.
          </p>
          <Button size="lg" onClick={() => setCreateOpen(true)}>Create your first Workspace</Button>
        </div>
      ) : (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {workspaces.map((ws) => (
            <Link key={ws.id} href={`/workspaces/${ws.id}/projects`}>
              <Card className="h-full hover:border-primary/50 transition-colors shadow-sm cursor-pointer group">
                <CardHeader>
                  <CardTitle className="group-hover:text-primary transition-colors flex items-center gap-2">
                    <Factory className="h-5 w-5 text-muted-foreground group-hover:text-primary" />
                    {ws.name}
                  </CardTitle>
                  <CardDescription className="line-clamp-2 mt-2 break-words">
                    {ws.description || "No description provided."}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="text-xs text-muted-foreground">
                    Created {new Date(ws.created_at).toLocaleDateString()}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
      
      <CreateWorkspaceDialog open={createOpen} onOpenChange={setCreateOpen} />
    </div>
  );
}
