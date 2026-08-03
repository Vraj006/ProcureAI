"use client";

import { useState, use } from "react";
import { useQuotations, useDeleteQuotation } from "@/features/quotations/api/queries";
import { useVendors } from "@/features/vendors/api/queries";
import { useExtraction } from "@/features/analysis/hooks/useAnalysisQueries";
import { QuotationResponse } from "@/services/api/types";
import { Loader2, Plus, FileBox } from "lucide-react";

import { Button } from "@/components/ui/button";
import { CreateQuotationDialog } from "@/features/quotations/components/CreateQuotationDialog";
import { QuotationTable } from "@/features/quotations/components/QuotationTable";
import { PDFUploadDropzone } from "@/features/quotations/components/PDFUploadDropzone";

export default function QuotationsTabPage({ params }: { params: Promise<{ workspaceId: string; projectId: string }> }) {
  const resolvedParams = use(params);
  const workspaceId = resolvedParams.workspaceId;
  const projectId = resolvedParams.projectId;

  // Dialog States
  const [createOpen, setCreateOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selectedQuotation, setSelectedQuotation] = useState<QuotationResponse | null>(null);

  const { data: quotationsData, isLoading: quotationsLoading } = useQuotations(workspaceId, projectId, 1, 50);
  const { data: vendorsData, isLoading: vendorsLoading } = useVendors(workspaceId, undefined, 1, 100);
  const { data: extractionData } = useExtraction(workspaceId, projectId);
  const { mutateAsync: deleteQuotation } = useDeleteQuotation();

  const handleUploadClick = (quotation: QuotationResponse) => {
    setSelectedQuotation(quotation);
    setUploadOpen(true);
  };

  const handleDelete = async (quotation: QuotationResponse) => {
    if (window.confirm(`Are you sure you want to delete quotation ${quotation.quotation_number}? This cannot be undone.`)) {
      await deleteQuotation({ workspaceId, projectId, quotationId: quotation.id });
    }
  };

  const isLoading = quotationsLoading || vendorsLoading;

  return (
    <div className="space-y-4">
      {/* Search and Actions */}
      <div className="flex justify-end items-center py-2">
        <Button onClick={() => setCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Quotation
        </Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center items-center py-24">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : !quotationsData || quotationsData.items.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 py-24 text-center border rounded-lg border-dashed bg-secondary/10 shadow-sm">
          <div className="h-16 w-16 bg-primary/10 rounded-full flex items-center justify-center mb-6">
            <FileBox className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-xl font-bold tracking-tight mb-2">No Quotations Uploaded</h3>
          <p className="text-muted-foreground max-w-sm text-sm mb-6">
            Link a vendor and upload your first PDF quotation to prepare this project for AI analysis.
          </p>
          <Button onClick={() => setCreateOpen(true)}>Create Quotation</Button>
        </div>
      ) : (
        <QuotationTable 
          quotations={quotationsData.items} 
          vendors={vendorsData?.items || []}
          extractions={extractionData || []}
          onUpload={handleUploadClick}
          onDelete={handleDelete}
        />
      )}

      {/* Overlays */}
      <CreateQuotationDialog 
        workspaceId={workspaceId} 
        projectId={projectId}
        open={createOpen} 
        onOpenChange={setCreateOpen} 
      />
      
      <PDFUploadDropzone 
        workspaceId={workspaceId}
        projectId={projectId}
        quotation={selectedQuotation}
        open={uploadOpen}
        onOpenChange={(op) => { setUploadOpen(op); if(!op) setSelectedQuotation(null); }}
      />
    </div>
  );
}
