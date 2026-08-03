import { RecommendationDashboard } from "@/features/analysis/components/RecommendationDashboard";

export default async function RecommendationPage({ params }: { params: Promise<{ workspaceId: string; projectId: string }> }) {
  const resolvedParams = await params;
  return (
    <div className="py-6">
      <RecommendationDashboard 
        workspaceId={resolvedParams.workspaceId} 
        projectId={resolvedParams.projectId} 
      />
    </div>
  );
}
