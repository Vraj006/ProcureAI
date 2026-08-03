import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileSearch, Layers } from "lucide-react";

interface ExtractionDetailsProps {
  quotationId: string;
  extractions: any[];
}

export function ExtractionDetails({ quotationId, extractions }: ExtractionDetailsProps) {
  const data = extractions?.find((e: any) => e.quotation_id === quotationId);

  if (!data) {
    return (
      <div className="py-8 flex flex-col items-center justify-center text-muted-foreground w-full">
        <FileSearch className="h-8 w-8 mb-2 opacity-50" />
        <p className="text-sm">No extraction data available for this quotation.</p>
        <p className="text-xs opacity-70">Run the AI analyzer to parse this document.</p>
      </div>
    );
  }

  const terms = data.terms || {};
  const items = data.items || [];

  return (
    <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in zoom-in-95 duration-200">
      <Card className="shadow-none border-dashed bg-background/50">
        <CardContent className="p-4">
          <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
            <Layers className="h-4 w-4 text-primary" />
            Commercial Terms
          </h4>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between border-b pb-1">
              <dt className="text-muted-foreground">Warranty Period</dt>
              <dd className="font-medium text-right">{terms.warranty || "N/A"}</dd>
            </div>
            <div className="flex justify-between border-b pb-1">
              <dt className="text-muted-foreground">Delivery Timeline</dt>
              <dd className="font-medium text-right">{terms.delivery_timeline || "N/A"}</dd>
            </div>
            <div className="flex justify-between pb-1">
              <dt className="text-muted-foreground">Payment Terms</dt>
              <dd className="font-medium text-right max-w-[200px] truncate" title={terms.payment_terms}>
                {terms.payment_terms || "N/A"}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>
      
      <Card className="shadow-none border-dashed bg-background/50">
        <CardContent className="p-4 flex flex-col h-full">
          <h4 className="text-sm font-semibold flex items-center gap-2 mb-3">
            <FileSearch className="h-4 w-4 text-primary" />
            Extracted Line Items ({items.length})
          </h4>
          
          <div className="flex-1 overflow-auto max-h-[140px] text-sm pr-2">
            {items.length === 0 ? (
              <p className="text-muted-foreground text-xs">No line items parsed.</p>
            ) : (
              <div className="space-y-3">
                {items.map((item: any, i: number) => (
                  <div key={i} className="flex justify-between items-start gap-4 pb-2 border-b last:border-0 last:pb-0">
                    <div>
                      <p className="font-medium text-[13px]">{item.description}</p>
                      <p className="text-xs text-muted-foreground max-w-[250px] truncate">{item.part_number || "Misc"}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-[13px]">${parseFloat(item.total_price || 0).toLocaleString()}</p>
                      <p className="text-xs text-muted-foreground">Qty: {item.quantity}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
