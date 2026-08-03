import { ReportsDashboard } from "@/features/analysis/components/ReportsDashboard";

export default async function ReportsPage({
  params,
}: {
  params: Promise<{ workspaceId: string; projectId: string }>;
}) {
  const resolvedParams = await params;
  return (
    <div className="pt-4">
      <ReportsDashboard workspaceId={resolvedParams.workspaceId} projectId={resolvedParams.projectId} />
    </div>
  );
}
