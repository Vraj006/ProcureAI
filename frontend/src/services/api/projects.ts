import { apiClient } from "./client";
import { ProjectCreate, ProjectResponse, ProjectUpdate, PaginatedProjectResponse } from "./types";

export const projectsApi = {
  listProjects: async (workspaceId: string, search?: string, page = 1, pageSize = 20): Promise<PaginatedProjectResponse> => {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    params.append("page", page.toString());
    params.append("page_size", pageSize.toString());

    const response = await apiClient.get<PaginatedProjectResponse>(`/workspaces/${workspaceId}/projects/?${params.toString()}`);
    return response.data;
  },

  createProject: async (workspaceId: string, data: ProjectCreate): Promise<ProjectResponse> => {
    const response = await apiClient.post<ProjectResponse>(`/workspaces/${workspaceId}/projects/`, data);
    return response.data;
  },

  getProject: async (workspaceId: string, projectId: string): Promise<ProjectResponse> => {
    const response = await apiClient.get<ProjectResponse>(`/workspaces/${workspaceId}/projects/${projectId}`);
    return response.data;
  },

  updateProject: async (workspaceId: string, projectId: string, data: ProjectUpdate): Promise<ProjectResponse> => {
    const response = await apiClient.put<ProjectResponse>(`/workspaces/${workspaceId}/projects/${projectId}`, data);
    return response.data;
  },

  deleteProject: async (workspaceId: string, projectId: string): Promise<void> => {
    await apiClient.delete(`/workspaces/${workspaceId}/projects/${projectId}`);
  },
};
