"use client";

import { useState, use, useEffect } from "react";
import { useVendors, useDeleteVendor } from "@/features/vendors/api/queries";
import { VendorResponse } from "@/services/api/types";
import { Loader2, Plus, Search, Building } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { CreateVendorDialog } from "@/features/vendors/components/CreateVendorDialog";
import { EditVendorDialog } from "@/features/vendors/components/EditVendorDialog";
import { VendorDetailsDrawer } from "@/features/vendors/components/VendorDetailsDrawer";
import { VendorTable } from "@/features/vendors/components/VendorTable";

export default function VendorsTabPage({ params }: { params: Promise<{ workspaceId: string; projectId: string }> }) {
  const resolvedParams = use(params);
  const workspaceId = resolvedParams.workspaceId;

  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
    }, 500);
    return () => clearTimeout(handler);
  }, [search]);

  // Dialog States
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedVendor, setSelectedVendor] = useState<VendorResponse | null>(null);

  const { data: vendorsData, isLoading } = useVendors(workspaceId, debouncedSearch || undefined, 1, 50);
  const { mutateAsync: deleteVendor } = useDeleteVendor();

  const handleEdit = (vendor: VendorResponse) => {
    setSelectedVendor(vendor);
    setEditOpen(true);
  };

  const handleView = (vendor: VendorResponse) => {
    setSelectedVendor(vendor);
    setDetailsOpen(true);
  };

  const handleDelete = async (vendor: VendorResponse) => {
    if (window.confirm(`Are you sure you want to delete ${vendor.company_name}? This cannot be undone.`)) {
      await deleteVendor({ workspaceId, vendorId: vendor.id });
    }
  };

  const handleDetailsEdit = () => {
    // Open edit dialog directly from details drawer
    setEditOpen(true);
  };

  return (
    <div className="space-y-4">
      {/* Search and Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 py-2">
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            type="search" 
            placeholder="Search vendors..." 
            className="pl-9 bg-background" 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Vendor
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : !vendorsData || vendorsData.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 py-24 text-center border rounded-lg border-dashed bg-secondary/10 shadow-sm">
          <div className="h-16 w-16 bg-primary/10 rounded-full flex items-center justify-center mb-6">
            <Building className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-xl font-bold tracking-tight mb-2">No Vendors Available</h3>
          <p className="text-muted-foreground max-w-sm text-sm mb-6">
            {search ? "No vendors matched your search." : "Start by registering your prospective vendors before uploading quotations."}
          </p>
          {!search && (
            <Button onClick={() => setCreateOpen(true)}>Add your first Vendor</Button>
          )}
        </div>
      ) : (
        <VendorTable 
          vendors={vendorsData.items} 
          onView={handleView}
          onEdit={handleEdit}
          onDelete={handleDelete}
        />
      )}

      {/* Overlays */}
      <CreateVendorDialog 
        workspaceId={workspaceId} 
        open={createOpen} 
        onOpenChange={setCreateOpen} 
      />
      <EditVendorDialog 
        workspaceId={workspaceId} 
        vendor={selectedVendor} 
        open={editOpen} 
        onOpenChange={(op) => { setEditOpen(op); if(!op) setSelectedVendor(null); }} 
      />
      <VendorDetailsDrawer 
        vendor={selectedVendor} 
        open={detailsOpen} 
        onOpenChange={(op) => { setDetailsOpen(op); if(!op && !editOpen) setSelectedVendor(null); }}
        onEditClick={handleDetailsEdit}
      />
    </div>
  );
}
