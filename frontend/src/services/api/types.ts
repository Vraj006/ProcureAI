export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface WorkspaceResponse {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceCreate {
  name: string;
  description?: string;
}

export interface WorkspaceUpdate {
  name?: string;
  description?: string;
}

export interface ProjectResponse {
  id: string;
  name: string;
  description?: string;
  status: string;
  metadata_?: Record<string, any>;
  workspace_id: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  status?: string;
  metadata?: Record<string, any>;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  status?: string;
  metadata?: Record<string, any>;
}

export interface PaginatedProjectResponse {
  items: ProjectResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface VendorBase {
  company_name: string;
  contact_person?: string | null;
  email?: string | null;
  phone?: string | null;
  website?: string | null;
  address?: string | null;
  country?: string | null;
  tax_number?: string | null;
  notes?: string | null;
  is_active?: boolean;
}

export interface VendorCreate extends VendorBase {}

export interface VendorUpdate extends Partial<VendorBase> {}

export interface VendorResponse extends VendorBase {
  id: string;
  workspace_id: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedVendorResponse {
  items: VendorResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface QuotationBase {
  quotation_number: string;
  quotation_date?: string | null;
  currency?: string;
  total_amount?: number | null;
}

export interface QuotationCreate extends QuotationBase {
  vendor_id: string;
}

export interface QuotationUpdate extends Partial<QuotationBase> {}

export interface QuotationResponse extends QuotationBase {
  id: string;
  project_id: string;
  vendor_id: string;
  uploaded_by: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  file_name?: string | null;
  file_path?: string | null;
  mime_type?: string | null;
  file_size?: number | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedQuotationResponse {
  items: QuotationResponse[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

