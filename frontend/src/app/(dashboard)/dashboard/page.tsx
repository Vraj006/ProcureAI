"use client";

import { useAuth } from "@/providers/auth-provider";
import { PageHeader } from "@/components/common/page-header";
import { StatCard } from "@/components/common/stat-card";
import { DashboardWelcome } from "@/features/dashboard/components/DashboardWelcome";
import { RecentProjectsCard } from "@/features/dashboard/components/RecentProjectsCard";
import { ActivityTimeline } from "@/features/dashboard/components/ActivityTimeline";
import { QuickActions } from "@/features/dashboard/components/QuickActions";
import { FolderKanban, Users, Clock, CheckCircle2, Factory } from "lucide-react";
import { useWorkspaces } from "@/features/workspaces/api/queries";
import { useProjects } from "@/features/projects/api/queries";

export default function DashboardPage() {
  const { user } = useAuth();
  const { data: workspaces, isLoading: wsLoading } = useWorkspaces();
  
  // To show recent projects, we will simply peek into the user's first workspace
  const defaultWorkspaceId = workspaces && workspaces.length > 0 ? workspaces[0].id : undefined;
  
  const { data: projectsData, isLoading: projLoading } = useProjects(
    defaultWorkspaceId as string,
    undefined,
    1,
    5
  );

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Dashboard" 
        description="Overview of your procurement projects and intelligence." 
      />
      
      <DashboardWelcome userName={user?.full_name || "Admin"} workspaceId={defaultWorkspaceId} />

      {/* KPI Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard 
          title="Total Workspaces" 
          value={wsLoading ? "..." : workspaces?.length.toString() || "0"} 
          icon={Factory} 
          description="active workspaces"
        />
        <StatCard 
          title="Total Projects" 
          value={projLoading ? "..." : projectsData?.total?.toString() || "0"} 
          icon={FolderKanban} 
          description={defaultWorkspaceId ? "in default workspace" : "no workspace found"} 
        />
        <StatCard 
          title="Pending Reviews" 
          value="0" 
          icon={Clock} 
          description="requires human approval"
        />
        <StatCard 
          title="Completed" 
          value="0" 
          icon={CheckCircle2} 
          description="fully processed"
        />
      </div>

      {/* Main content grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <div className="lg:col-span-4 space-y-6">
          <RecentProjectsCard 
             projects={projectsData?.items} 
             workspaceId={defaultWorkspaceId} 
             isLoading={projLoading} 
          />
        </div>
        <div className="lg:col-span-3 space-y-6">
          <QuickActions workspaceId={defaultWorkspaceId} />
          <ActivityTimeline />
        </div>
      </div>
    </div>
  );
}
