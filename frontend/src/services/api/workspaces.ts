import { apiClient } from "./client";
import { WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate } from "./types";

export const workspacesApi = {
  listWorkspaces: async (): Promise<WorkspaceResponse[]> => {
    const response = await apiClient.get<WorkspaceResponse[]>("/workspaces/");
    return response.data;
  },

  createWorkspace: async (data: WorkspaceCreate): Promise<WorkspaceResponse> => {
    const response = await apiClient.post<WorkspaceResponse>("/workspaces/", data);
    return response.data;
  },

  getWorkspace: async (id: string): Promise<WorkspaceResponse> => {
    const response = await apiClient.get<WorkspaceResponse>(`/workspaces/${id}`);
    return response.data;
  },

  updateWorkspace: async (id: string, data: WorkspaceUpdate): Promise<WorkspaceResponse> => {
    const response = await apiClient.put<WorkspaceResponse>(`/workspaces/${id}`, data);
    return response.data;
  },

  deleteWorkspace: async (id: string): Promise<void> => {
    await apiClient.delete(`/workspaces/${id}`);
  },
};
