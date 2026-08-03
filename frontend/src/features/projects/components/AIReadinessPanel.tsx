import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Check, X, Sparkles, BrainCircuit } from "lucide-react";
import { cn } from "@/lib/utils";

interface AIReadinessPanelProps {
  hasVendors: boolean;
  hasQuotations: boolean;
  allQuotationsUploaded: boolean;
  onAnalyze: () => void;
}

export function AIReadinessPanel({ hasVendors, hasQuotations, allQuotationsUploaded, onAnalyze }: AIReadinessPanelProps) {
  
  const isReady = hasVendors && hasQuotations && allQuotationsUploaded;

  return (
    <Card className="border-primary/20 bg-gradient-to-b from-background to-primary/5 shadow-sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-xl">
          <BrainCircuit className="h-5 w-5 text-primary" />
          AI Analysis Readiness
        </CardTitle>
        <CardDescription>
          Fulfill requirements to unlock ProcureAI automated insights.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className={cn("flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold shrink-0 transition-colors",
               hasVendors ? "bg-emerald-100 text-emerald-600" : "bg-muted text-muted-foreground")}>
              {hasVendors ? <Check className="h-3.5 w-3.5" /> : <X className="h-3.5 w-3.5" />}
            </div>
            <p className={cn("text-sm", hasVendors ? "font-medium" : "text-muted-foreground")}>
              At least one Vendor registered
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <div className={cn("flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold shrink-0 transition-colors",
               hasQuotations ? "bg-emerald-100 text-emerald-600" : "bg-muted text-muted-foreground")}>
              {hasQuotations ? <Check className="h-3.5 w-3.5" /> : <X className="h-3.5 w-3.5" />}
            </div>
            <p className={cn("text-sm", hasQuotations ? "font-medium" : "text-muted-foreground")}>
              At least one Quotation created
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className={cn("flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold shrink-0 transition-colors",
               allQuotationsUploaded && hasQuotations ? "bg-emerald-100 text-emerald-600" : "bg-muted text-muted-foreground")}>
              {allQuotationsUploaded && hasQuotations ? <Check className="h-3.5 w-3.5" /> : <X className="h-3.5 w-3.5" />}
            </div>
            <p className={cn("text-sm", allQuotationsUploaded && hasQuotations ? "font-medium" : "text-muted-foreground")}>
              All Quotations have uploaded documents
            </p>
          </div>
        </div>

        <div className="pt-4 border-t">
          <Button 
            className="w-full relative overflow-hidden group" 
            disabled={!isReady}
            size="lg"
            onClick={onAnalyze}
          >
            {isReady && (
              <span className="absolute inset-0 bg-primary-foreground/20 w-0 group-hover:w-full transition-all duration-300 ease-out z-0" />
            )}
            <span className="relative z-10 flex items-center gap-2 font-semibold tracking-wide">
              <Sparkles className="h-4 w-4" /> 
              {isReady ? "Analyze Procurement" : "Analysis Locked"}
            </span>
          </Button>
          {!isReady && (
            <p className="text-center text-xs text-muted-foreground font-medium mt-3">
              Resolve pending items to commence mapping.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
