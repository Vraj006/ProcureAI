import { ReviewDashboard } from "@/features/analysis/components/ReviewDashboard";

export default async function ReviewPage({ params }: { params: Promise<{ workspaceId: string; projectId: string }> }) {
  const resolvedParams = await params;
  return (
    <div className="py-6">
      <ReviewDashboard 
        workspaceId={resolvedParams.workspaceId} 
        projectId={resolvedParams.projectId} 
      />
    </div>
  );
}
