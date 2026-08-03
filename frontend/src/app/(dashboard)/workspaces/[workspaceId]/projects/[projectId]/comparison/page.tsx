import { ComparisonDashboard } from "@/features/analysis/components/ComparisonDashboard";

export default async function ComparisonPage({ params }: { params: Promise<{ workspaceId: string; projectId: string }> }) {
  const resolvedParams = await params;
  return (
    <div className="py-6">
      <ComparisonDashboard 
        workspaceId={resolvedParams.workspaceId} 
        projectId={resolvedParams.projectId} 
      />
    </div>
  );
}
