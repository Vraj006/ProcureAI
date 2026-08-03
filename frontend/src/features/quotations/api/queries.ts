import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { quotationsApi } from "@/services/api/quotations";
import { QuotationCreate, QuotationUpdate } from "@/services/api/types";
import { toast } from "sonner";

export const quotationKeys = {
  all: (workspaceId: string, projectId: string) => ["workspaces", workspaceId, "projects", projectId, "quotations"] as const,
  lists: (workspaceId: string, projectId: string) => [...quotationKeys.all(workspaceId, projectId), "list"] as const,
  list: (workspaceId: string, projectId: string, page?: number) => 
    [...quotationKeys.lists(workspaceId, projectId), { page }] as const,
  details: (workspaceId: string, projectId: string) => [...quotationKeys.all(workspaceId, projectId), "detail"] as const,
  detail: (workspaceId: string, projectId: string, quotationId: string) => 
    [...quotationKeys.details(workspaceId, projectId), quotationId] as const,
};

export function useQuotations(workspaceId: string, projectId: string, page = 1, pageSize = 50) {
  return useQuery({
    queryKey: quotationKeys.list(workspaceId, projectId, page),
    queryFn: () => quotationsApi.listQuotations(workspaceId, projectId, page, pageSize),
    enabled: !!workspaceId && !!projectId,
  });
}

export function useQuotation(workspaceId: string, projectId: string, quotationId: string) {
  return useQuery({
    queryKey: quotationKeys.detail(workspaceId, projectId, quotationId),
    queryFn: () => quotationsApi.getQuotation(workspaceId, projectId, quotationId),
    enabled: !!workspaceId && !!projectId && !!quotationId,
  });
}

export function useCreateQuotation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ workspaceId, projectId, data }: { workspaceId: string; projectId: string; data: QuotationCreate }) => 
      quotationsApi.createQuotation(workspaceId, projectId, data),
    onSuccess: (data, variables) => {
      toast.success("Quotation placeholder created successfully");
      queryClient.invalidateQueries({ queryKey: quotationKeys.lists(variables.workspaceId, variables.projectId) });
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || "Failed to create quotation placeholder";
      toast.error(typeof msg === "string" ? msg : JSON.stringify(msg));
    },
  });
}

export function useUpdateQuotation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ workspaceId, projectId, quotationId, data }: { workspaceId: string; projectId: string; quotationId: string; data: QuotationUpdate }) => 
      quotationsApi.updateQuotation(workspaceId, projectId, quotationId, data),
    onSuccess: (data, variables) => {
      toast.success("Quotation updated");
      queryClient.invalidateQueries({ queryKey: quotationKeys.detail(variables.workspaceId, variables.projectId, variables.quotationId) });
      queryClient.invalidateQueries({ queryKey: quotationKeys.lists(variables.workspaceId, variables.projectId) });
    },
    onError: () => {
      toast.error("Failed to update quotation");
    },
  });
}

export function useDeleteQuotation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ workspaceId, projectId, quotationId }: { workspaceId: string; projectId: string; quotationId: string }) => 
      quotationsApi.deleteQuotation(workspaceId, projectId, quotationId),
    onSuccess: (data, variables) => {
      toast.success("Quotation deleted");
      queryClient.invalidateQueries({ queryKey: quotationKeys.lists(variables.workspaceId, variables.projectId) });
    },
    onError: () => {
      toast.error("Failed to delete quotation");
    },
  });
}

export function useUploadPDF() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ 
      workspaceId, 
      projectId, 
      quotationId, 
      file,
      onProgress
    }: { 
      workspaceId: string; 
      projectId: string; 
      quotationId: string; 
      file: File;
      onProgress?: (event: any) => void;
    }) => 
      quotationsApi.uploadPDF(workspaceId, projectId, quotationId, file, onProgress),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: quotationKeys.detail(variables.workspaceId, variables.projectId, variables.quotationId) });
      queryClient.invalidateQueries({ queryKey: quotationKeys.lists(variables.workspaceId, variables.projectId) });
    },
  });
}
