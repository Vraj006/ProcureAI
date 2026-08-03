import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Check, Clock, AlertCircle } from "lucide-react";

const steps = [
  { id: "extraction", label: "Document Extraction", status: "complete", desc: "Text & tabular data parsed." },
  { id: "comparison", label: "Commercial Comparison", status: "complete", desc: "Pricing and terms analyzed." },
  { id: "compliance", label: "Compliance Validation", status: "pending", desc: "Awaiting execution." },
  { id: "recommendation", label: "AI Recommendation", status: "pending", desc: "Pending comparison results." },
  { id: "review", label: "Human Review", status: "pending", desc: "Requires final approval." },
];

export function WorkflowStepper() {
  return (
    <Card className="shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg">Analysis Workflow</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative pl-6 space-y-6 before:absolute before:inset-y-0 before:left-[11px] before:w-px before:bg-border">
          {steps.map((step, index) => {
            const isComplete = step.status === "complete";
            const isActive = step.status === "in_progress";
            
            return (
              <div key={step.id} className="relative flex gap-4">
                <div className="absolute -left-[30px] rounded-full bg-card ring-8 ring-card">
                  {isComplete ? (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500 text-white">
                      <Check className="h-3 w-3" />
                    </div>
                  ) : isActive ? (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full border-2 border-primary">
                      <div className="h-2 w-2 rounded-full bg-primary" />
                    </div>
                  ) : (
                    <div className="flex h-5 w-5 items-center justify-center rounded-full border-2 border-muted-foreground/30 bg-secondary">
                      <Clock className="h-3 w-3 text-muted-foreground" />
                    </div>
                  )}
                </div>
                <div>
                  <h4 className={`text-sm font-semibold ${isComplete ? 'text-foreground' : 'text-muted-foreground'}`}>
                    {step.label}
                  </h4>
                  <p className="text-xs text-muted-foreground mt-0.5">{step.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
