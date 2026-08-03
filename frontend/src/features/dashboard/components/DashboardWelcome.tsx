import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";
import Link from "next/link";

export function DashboardWelcome({ userName, workspaceId }: { userName: string, workspaceId?: string }) {
  const href = workspaceId ? `/workspaces/${workspaceId}/projects/new` : "/workspaces";

  return (
    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 p-6 bg-primary text-primary-foreground rounded-lg shadow-sm">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold tracking-tight">Welcome back, {userName}</h1>
        <p className="text-primary-foreground/80 max-w-xl">
          Here is what is happening with your procurement intelligence today.
        </p>
      </div>
      <div>
        <Button variant="secondary" className="whitespace-nowrap" asChild>
          <Link href={href}>
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Link>
        </Button>
      </div>
    </div>
  );
}
