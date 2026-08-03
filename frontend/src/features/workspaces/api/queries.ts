import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { workspacesApi } from "@/services/api/workspaces";
import { WorkspaceCreate, WorkspaceUpdate } from "@/services/api/types";
import { toast } from "sonner";

export const workspaceKeys = {
  all: ["workspaces"] as const,
  lists: () => [...workspaceKeys.all, "list"] as const,
  list: () => [...workspaceKeys.lists()] as const,
  details: () => [...workspaceKeys.all, "detail"] as const,
  detail: (id: string) => [...workspaceKeys.details(), id] as const,
};

export function useWorkspaces() {
  return useQuery({
    queryKey: workspaceKeys.list(),
    queryFn: () => workspacesApi.listWorkspaces(),
  });
}

export function useWorkspace(id: string) {
  return useQuery({
    queryKey: workspaceKeys.detail(id),
    queryFn: () => workspacesApi.getWorkspace(id),
    enabled: !!id,
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: WorkspaceCreate) => workspacesApi.createWorkspace(data),
    onSuccess: () => {
      toast.success("Workspace created successfully");
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || "Failed to create workspace";
      toast.error(typeof msg === "string" ? msg : JSON.stringify(msg));
    },
  });
}

export function useUpdateWorkspace() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkspaceUpdate }) => 
      workspacesApi.updateWorkspace(id, data),
    onSuccess: (data, variables) => {
      toast.success("Workspace updated");
      queryClient.invalidateQueries({ queryKey: workspaceKeys.detail(variables.id) });
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
    onError: () => {
      toast.error("Failed to update workspace");
    },
  });
}

export function useDeleteWorkspace() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => workspacesApi.deleteWorkspace(id),
    onSuccess: () => {
      toast.success("Workspace deleted");
      queryClient.invalidateQueries({ queryKey: workspaceKeys.lists() });
    },
    onError: () => {
      toast.error("Failed to delete workspace");
    },
  });
}
