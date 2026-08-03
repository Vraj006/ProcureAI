import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { vendorsApi } from "@/services/api/vendors";
import { VendorCreate, VendorUpdate } from "@/services/api/types";
import { toast } from "sonner";

export const vendorKeys = {
  all: (workspaceId: string) => ["workspaces", workspaceId, "vendors"] as const,
  lists: (workspaceId: string) => [...vendorKeys.all(workspaceId), "list"] as const,
  list: (workspaceId: string, search?: string, page?: number) => 
    [...vendorKeys.lists(workspaceId), { search, page }] as const,
  details: (workspaceId: string) => [...vendorKeys.all(workspaceId), "detail"] as const,
  detail: (workspaceId: string, vendorId: string) => 
    [...vendorKeys.details(workspaceId), vendorId] as const,
};

export function useVendors(workspaceId: string, search?: string, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: vendorKeys.list(workspaceId, search, page),
    queryFn: () => vendorsApi.listVendors(workspaceId, search, page, pageSize),
    enabled: !!workspaceId,
  });
}

export function useVendor(workspaceId: string, vendorId: string) {
  return useQuery({
    queryKey: vendorKeys.detail(workspaceId, vendorId),
    queryFn: () => vendorsApi.getVendor(workspaceId, vendorId),
    enabled: !!workspaceId && !!vendorId,
  });
}

export function useCreateVendor() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ workspaceId, data }: { workspaceId: string; data: VendorCreate }) => 
      vendorsApi.createVendor(workspaceId, data),
    onSuccess: (data, variables) => {
      toast.success("Vendor created successfully");
      queryClient.invalidateQueries({ queryKey: vendorKeys.lists(variables.workspaceId) });
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || "Failed to create vendor";
      toast.error(typeof msg === "string" ? msg : JSON.stringify(msg));
    },
  });
}

export function useUpdateVendor() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ workspaceId, vendorId, data }: { workspaceId: string; vendorId: string; data: VendorUpdate }) => 
      vendorsApi.updateVendor(workspaceId, vendorId, data),
    onSuccess: (data, variables) => {
      toast.success("Vendor updated successfully");
      queryClient.invalidateQueries({ queryKey: vendorKeys.detail(variables.workspaceId, variables.vendorId) });
      queryClient.invalidateQueries({ queryKey: vendorKeys.lists(variables.workspaceId) });
    },
    onError: () => {
      toast.error("Failed to update vendor");
    },
  });
}

export function useDeleteVendor() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ workspaceId, vendorId }: { workspaceId: string; vendorId: string }) => 
      vendorsApi.deleteVendor(workspaceId, vendorId),
    onSuccess: (data, variables) => {
      toast.success("Vendor deleted");
      queryClient.invalidateQueries({ queryKey: vendorKeys.lists(variables.workspaceId) });
    },
    onError: () => {
      toast.error("Failed to delete vendor");
    },
  });
}
