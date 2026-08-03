import { AnalysisDashboard } from "@/features/analysis/components/AnalysisDashboard";

export default async function AnalysisPage({ params }: { params: Promise<{ workspaceId: string; projectId: string }> }) {
  const resolvedParams = await params;
  
  return (
    <div className="py-6">
      <AnalysisDashboard 
        workspaceId={resolvedParams.workspaceId} 
        projectId={resolvedParams.projectId} 
      />
    </div>
  );
}
