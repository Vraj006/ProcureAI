import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { analysisApi, ReviewSubmitPayload } from "@/services/api/analysis";

// Query Keys
export const analysisKeys = {
  all: ["analysis"] as const,
  workflow: (projectId: string) => [...analysisKeys.all, "workflow", projectId] as const,
  extraction: (projectId: string) => [...analysisKeys.all, "extraction", projectId] as const,
  comparison: (projectId: string) => [...analysisKeys.all, "comparison", projectId] as const,
  compliance: (projectId: string) => [...analysisKeys.all, "compliance", projectId] as const,
  recommendation: (projectId: string) => [...analysisKeys.all, "recommendation", projectId] as const,
};

// ------------------------------------------------------------------
// Queries
// ------------------------------------------------------------------

export function useWorkflowStatus(workspaceId: string, projectId: string) {
  return useQuery({
    queryKey: analysisKeys.workflow(projectId),
    queryFn: () => analysisApi.getWorkflowStatus(workspaceId, projectId),
    refetchInterval: (query) => {
      // Poll every 3 seconds if status is pending
      return query.state.data?.status === "pending" ? 3000 : false;
    },
  });
}

export function useExtraction(workspaceId: string, projectId: string) {
  return useQuery({
    queryKey: analysisKeys.extraction(projectId),
    queryFn: () => analysisApi.getExtraction(workspaceId, projectId),
  });
}

export function useComparison(workspaceId: string, projectId: string) {
  return useQuery({
    queryKey: analysisKeys.comparison(projectId),
    queryFn: () => analysisApi.getComparison(workspaceId, projectId),
  });
}

export function useCompliance(workspaceId: string, projectId: string) {
  return useQuery({
    queryKey: analysisKeys.compliance(projectId),
    queryFn: () => analysisApi.getCompliance(workspaceId, projectId),
  });
}

export function useRecommendation(workspaceId: string, projectId: string) {
  return useQuery({
    queryKey: analysisKeys.recommendation(projectId),
    queryFn: () => analysisApi.getRecommendation(workspaceId, projectId),
  });
}

// ------------------------------------------------------------------
// Mutations
// ------------------------------------------------------------------

export function useStartAnalysis(workspaceId: string, projectId: string) {
  const qc = useQueryClient();
  
  return useMutation({
    mutationFn: () => analysisApi.startAnalysis(workspaceId, projectId),
    onSuccess: () => {
      // Invalidate to forcefully trigger updates in the UI
      qc.invalidateQueries({ queryKey: analysisKeys.workflow(projectId) });
      qc.invalidateQueries({ queryKey: analysisKeys.extraction(projectId) });
      qc.invalidateQueries({ queryKey: analysisKeys.comparison(projectId) });
      qc.invalidateQueries({ queryKey: analysisKeys.compliance(projectId) });
      qc.invalidateQueries({ queryKey: analysisKeys.recommendation(projectId) });
    },
  });
}

export function useSubmitReview(workspaceId: string, projectId: string) {
  const qc = useQueryClient();
  
  return useMutation({
    mutationFn: (payload: ReviewSubmitPayload) => analysisApi.submitReview(workspaceId, projectId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: analysisKeys.workflow(projectId) });
      qc.invalidateQueries({ queryKey: analysisKeys.recommendation(projectId) });
    },
  });
}
