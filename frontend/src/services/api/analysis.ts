import { apiClient } from "./client";

export interface WorkflowStatusResponse {
  project_id: string;
  status: "pending" | "completed";
  steps: {
    document_processing: "pending" | "completed" | "failed";
    extraction: "pending" | "completed" | "failed";
    comparison: "pending" | "completed" | "failed";
    compliance: "pending" | "completed" | "failed";
    recommendation: "pending" | "completed" | "failed";
    human_review: "pending" | "approved" | "rejected" | "requires_changes";
  };
}

export interface ReviewSubmitPayload {
  status: "approved" | "rejected" | "requires_changes";
  comments: string;
}

export const analysisApi = {
  /** Trigger LangGraph Analysis */
  startAnalysis: async (workspaceId: string, projectId: string) => {
    const { data } = await apiClient.post(
      `/workspaces/${workspaceId}/projects/${projectId}/analyze`
    );
    return data;
  },

  /** Get LangGraph Workflow Status */
  getWorkflowStatus: async (workspaceId: string, projectId: string): Promise<WorkflowStatusResponse> => {
    const { data } = await apiClient.get(
      `/workspaces/${workspaceId}/projects/${projectId}/workflow`
    );
    return data;
  },

  /** Get Extraction Results */
  getExtraction: async (workspaceId: string, projectId: string) => {
    const { data } = await apiClient.get(
      `/workspaces/${workspaceId}/projects/${projectId}/extraction`
    );
    return data;
  },

  /** Get Comparison Results */
  getComparison: async (workspaceId: string, projectId: string) => {
    const { data } = await apiClient.get(
      `/workspaces/${workspaceId}/projects/${projectId}/comparison`
    );
    return data;
  },

  /** Get Compliance Results */
  getCompliance: async (workspaceId: string, projectId: string) => {
    const { data } = await apiClient.get(
      `/workspaces/${workspaceId}/projects/${projectId}/compliance`
    );
    return data;
  },

  /** Get Recommendation Results */
  getRecommendation: async (workspaceId: string, projectId: string) => {
    const { data } = await apiClient.get(
      `/workspaces/${workspaceId}/projects/${projectId}/recommendation`
    );
    return data;
  },

  /** Submit Human Review */
  submitReview: async (workspaceId: string, projectId: string, payload: ReviewSubmitPayload) => {
    const { data } = await apiClient.post(
      `/workspaces/${workspaceId}/projects/${projectId}/review`,
      payload
    );
    return data;
  },

  downloadPdfReport: async (workspaceId: string, projectId: string) => {
    const response = await apiClient.get(
      `/workspaces/${workspaceId}/projects/${projectId}/report/pdf`,
      { responseType: "blob" }
    );
    return response.data;
  },

  downloadExcelReport: async (workspaceId: string, projectId: string) => {
    const response = await apiClient.get(
      `/workspaces/${workspaceId}/projects/${projectId}/report/excel`,
      { responseType: "blob" }
    );
    return response.data;
  },
};
