import { apiClient } from "./client";
import { QuotationCreate, QuotationResponse, QuotationUpdate, PaginatedQuotationResponse } from "./types";
import { AxiosRequestConfig } from "axios";

export const quotationsApi = {
  listQuotations: async (workspaceId: string, projectId: string, page = 1, pageSize = 20): Promise<PaginatedQuotationResponse> => {
    const params = new URLSearchParams();
    params.append("page", page.toString());
    params.append("page_size", pageSize.toString());

    const response = await apiClient.get<PaginatedQuotationResponse>(`/workspaces/${workspaceId}/projects/${projectId}/quotations/?${params.toString()}`);
    return response.data;
  },

  createQuotation: async (workspaceId: string, projectId: string, data: QuotationCreate): Promise<QuotationResponse> => {
    const response = await apiClient.post<QuotationResponse>(`/workspaces/${workspaceId}/projects/${projectId}/quotations/`, data);
    return response.data;
  },

  getQuotation: async (workspaceId: string, projectId: string, quotationId: string): Promise<QuotationResponse> => {
    const response = await apiClient.get<QuotationResponse>(`/workspaces/${workspaceId}/projects/${projectId}/quotations/${quotationId}`);
    return response.data;
  },

  updateQuotation: async (workspaceId: string, projectId: string, quotationId: string, data: QuotationUpdate): Promise<QuotationResponse> => {
    const response = await apiClient.put<QuotationResponse>(`/workspaces/${workspaceId}/projects/${projectId}/quotations/${quotationId}`, data);
    return response.data;
  },

  deleteQuotation: async (workspaceId: string, projectId: string, quotationId: string): Promise<void> => {
    await apiClient.delete(`/workspaces/${workspaceId}/projects/${projectId}/quotations/${quotationId}`);
  },

  uploadPDF: async (
    workspaceId: string, 
    projectId: string, 
    quotationId: string, 
    file: File,
    onProgress?: (progressEvent: any) => void
  ): Promise<any> => {
    const formData = new FormData();
    formData.append("file", file);

    const config: AxiosRequestConfig = {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: onProgress,
    };

    const response = await apiClient.post(
      `/workspaces/${workspaceId}/projects/${projectId}/quotations/${quotationId}/upload`,
      formData,
      config
    );
    return response.data;
  }
};
