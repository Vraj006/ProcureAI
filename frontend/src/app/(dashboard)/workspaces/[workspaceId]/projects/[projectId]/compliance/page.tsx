import { ComplianceDashboard } from "@/features/analysis/components/ComplianceDashboard";

export default async function CompliancePage({ params }: { params: Promise<{ workspaceId: string; projectId: string }> }) {
  const resolvedParams = await params;
  return (
    <div className="py-6">
      <ComplianceDashboard 
        workspaceId={resolvedParams.workspaceId} 
        projectId={resolvedParams.projectId} 
      />
    </div>
  );
}
