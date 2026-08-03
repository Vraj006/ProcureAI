import { apiClient } from "./client";
import { VendorCreate, VendorResponse, VendorUpdate, PaginatedVendorResponse } from "./types";

export const vendorsApi = {
  listVendors: async (workspaceId: string, search?: string, page = 1, pageSize = 20): Promise<PaginatedVendorResponse> => {
    const params = new URLSearchParams();
    if (search) params.append("search", search);
    params.append("page", page.toString());
    params.append("page_size", pageSize.toString());

    const response = await apiClient.get<PaginatedVendorResponse>(`/workspaces/${workspaceId}/vendors/?${params.toString()}`);
    return response.data;
  },

  createVendor: async (workspaceId: string, data: VendorCreate): Promise<VendorResponse> => {
    const response = await apiClient.post<VendorResponse>(`/workspaces/${workspaceId}/vendors/`, data);
    return response.data;
  },

  getVendor: async (workspaceId: string, vendorId: string): Promise<VendorResponse> => {
    const response = await apiClient.get<VendorResponse>(`/workspaces/${workspaceId}/vendors/${vendorId}`);
    return response.data;
  },

  updateVendor: async (workspaceId: string, vendorId: string, data: VendorUpdate): Promise<VendorResponse> => {
    const response = await apiClient.put<VendorResponse>(`/workspaces/${workspaceId}/vendors/${vendorId}`, data);
    return response.data;
  },

  deleteVendor: async (workspaceId: string, vendorId: string): Promise<void> => {
    await apiClient.delete(`/workspaces/${workspaceId}/vendors/${vendorId}`);
  },
};
