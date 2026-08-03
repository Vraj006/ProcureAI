import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export function PageLoader({ className }: { className?: string }) {
  return (
    <div className={cn("flex flex-col items-center justify-center w-full h-64", className)}>
      <Loader2 className="w-8 h-8 animate-spin text-primary" />
      <p className="mt-4 text-sm text-muted-foreground">Loading data...</p>
    </div>
  );
}
