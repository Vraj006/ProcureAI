import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { projectsApi } from "@/services/api/projects";
import { ProjectCreate, ProjectUpdate } from "@/services/api/types";
import { toast } from "sonner";

export const projectKeys = {
  all: (workspaceId: string) => ["workspaces", workspaceId, "projects"] as const,
  lists: (workspaceId: string) => [...projectKeys.all(workspaceId), "list"] as const,
  list: (workspaceId: string, search?: string, page?: number) => 
    [...projectKeys.lists(workspaceId), { search, page }] as const,
  details: (workspaceId: string) => [...projectKeys.all(workspaceId), "detail"] as const,
  detail: (workspaceId: string, projectId: string) => 
    [...projectKeys.details(workspaceId), projectId] as const,
};

export function useProjects(workspaceId: string, search?: string, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: projectKeys.list(workspaceId, search, page),
    queryFn: () => projectsApi.listProjects(workspaceId, search, page, pageSize),
    enabled: !!workspaceId,
  });
}

export function useProject(workspaceId: string, projectId: string) {
  return useQuery({
    queryKey: projectKeys.detail(workspaceId, projectId),
    queryFn: () => projectsApi.getProject(workspaceId, projectId),
    enabled: !!workspaceId && !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ workspaceId, data }: { workspaceId: string; data: ProjectCreate }) => 
      projectsApi.createProject(workspaceId, data),
    onSuccess: (data, variables) => {
      toast.success("Project created successfully");
      queryClient.invalidateQueries({ queryKey: projectKeys.lists(variables.workspaceId) });
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || "Failed to create project";
      toast.error(typeof msg === "string" ? msg : JSON.stringify(msg));
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ workspaceId, projectId }: { workspaceId: string; projectId: string }) => 
      projectsApi.deleteProject(workspaceId, projectId),
    onSuccess: (data, variables) => {
      toast.success("Project deleted");
      queryClient.invalidateQueries({ queryKey: projectKeys.lists(variables.workspaceId) });
    },
    onError: () => {
      toast.error("Failed to delete project");
    },
  });
}
