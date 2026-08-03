import { QuotationResponse, VendorResponse } from "@/services/api/types";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { buttonVariants } from "@/components/ui/button";
import { MoreHorizontal, FileText, Trash, UploadCloud, RefreshCw, ChevronDown, ChevronRight, Layers } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { ExtractionDetails } from "@/features/analysis/components/ExtractionDetails";

interface QuotationTableProps {
  quotations: QuotationResponse[];
  vendors: VendorResponse[];
  extractions?: any[];
  onUpload: (quotation: QuotationResponse) => void;
  onDelete: (quotation: QuotationResponse) => void;
}

export function QuotationTable({ quotations, vendors, extractions = [], onUpload, onDelete }: QuotationTableProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const getVendorName = (vendorId: string) => {
    const v = vendors.find(v => v.id === vendorId);
    return v ? v.company_name : "Unknown Vendor";
  };

  return (
    <div className="rounded-md border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-10"></TableHead>
            <TableHead>Quotation No.</TableHead>
            <TableHead>Vendor</TableHead>
            <TableHead>File</TableHead>
            <TableHead>Amount</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-[80px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {quotations.map((quotation) => (
            <>
            <TableRow 
              key={quotation.id} 
              className={cn("transition-colors", expanded === quotation.id && "bg-muted/20")}
            >
              <TableCell>
                <div 
                  className={buttonVariants({ variant: "ghost", size: "sm", className: "h-6 w-6 p-0 cursor-pointer" })}
                  onClick={() => setExpanded(expanded === quotation.id ? null : quotation.id)}
                >
                  {expanded === quotation.id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </div>
              </TableCell>
              <TableCell className="font-medium text-sm">
                {quotation.quotation_number}
              </TableCell>
              <TableCell className="text-sm">
                {getVendorName(quotation.vendor_id)}
              </TableCell>
              <TableCell>
                {quotation.file_name ? (
                  <div className="flex items-center text-sm font-medium text-blue-600">
                    <FileText className="h-4 w-4 mr-1.5" />
                    <span className="truncate max-w-[150px]" title={quotation.file_name}>
                      {quotation.file_name}
                    </span>
                  </div>
                ) : (
                  <Badge variant="secondary" className="bg-amber-100 text-amber-700 hover:bg-amber-100 font-normal">
                    Pending Upload
                  </Badge>
                )}
              </TableCell>
              <TableCell className="text-sm">
                {quotation.total_amount ? (
                   <span className="font-medium">{quotation.currency} {parseFloat(quotation.total_amount.toString()).toLocaleString()}</span>
                ) : (
                   <span className="text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell>
               <Badge className={cn(
                 quotation.status === "FAILED" && "bg-destructive text-destructive-foreground",
                 quotation.status === "COMPLETED" && "bg-emerald-100 text-emerald-700",
                 quotation.status === "PROCESSING" && "bg-blue-100 text-blue-700",
               )} variant={quotation.status === "PENDING" ? "outline" : "secondary"}>
                 {quotation.status}
               </Badge>
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger className={buttonVariants({ variant: "ghost", className: "h-8 w-8 p-0" })}>
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onUpload(quotation)}>
                      {quotation.file_name ? (
                        <><RefreshCw className="mr-2 h-4 w-4" /> Replace Document</>
                      ) : (
                        <><UploadCloud className="mr-2 h-4 w-4" /> Upload PDF</>
                      )}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      onClick={() => onDelete(quotation)}
                      className="text-destructive focus:text-destructive focus:bg-destructive/10"
                    >
                      <Trash className="mr-2 h-4 w-4" /> Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
            {expanded === quotation.id && (
              <TableRow className="bg-muted/10">
                <TableCell colSpan={7} className="p-0 border-b">
                  <ExtractionDetails quotationId={quotation.id} extractions={extractions} />
                </TableCell>
              </TableRow>
            )}
            </>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
