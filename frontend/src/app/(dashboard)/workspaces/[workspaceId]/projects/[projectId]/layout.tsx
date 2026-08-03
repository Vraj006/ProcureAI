import { ProjectHeader } from "@/features/projects/components/ProjectHeader";
import { ProjectTabs } from "@/features/projects/components/ProjectTabs";

export default async function ProjectDetailLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ workspaceId: string; projectId: string }>;
}) {
  const resolvedParams = await params;

  return (
    <div className="space-y-6">
      <ProjectHeader workspaceId={resolvedParams.workspaceId} projectId={resolvedParams.projectId} />
      <ProjectTabs workspaceId={resolvedParams.workspaceId} projectId={resolvedParams.projectId} />
      <div className="pt-2">
        {children}
      </div>
    </div>
  );
}
