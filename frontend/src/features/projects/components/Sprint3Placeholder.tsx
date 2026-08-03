import { Lock } from "lucide-react";

export function Sprint3Placeholder({ featureName }: { featureName: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-16 py-24 text-center border rounded-lg border-dashed bg-secondary/10 shadow-sm mt-4">
      <div className="h-16 w-16 bg-primary/10 rounded-full flex items-center justify-center mb-6">
        <Lock className="h-8 w-8 text-primary" />
      </div>
      <h3 className="text-xl font-bold tracking-tight mb-2">
        {featureName} Dashboard
      </h3>
      <p className="text-muted-foreground max-w-sm mb-6">
        This premium AI feature is currently under development. It will be available in Sprint 3.
      </p>
    </div>
  );
}
