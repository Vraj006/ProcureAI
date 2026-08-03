import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, ListFilter, Users, Settings } from "lucide-react";
import Link from "next/link";

export function QuickActions({ workspaceId }: { workspaceId?: string }) {
  const actions = [
    {
      title: "New Project",
      href: workspaceId ? `/workspaces/${workspaceId}/projects/new` : "/workspaces",
      icon: Plus,
    },
    {
      title: "All Workspaces",
      href: "/workspaces",
      icon: ListFilter,
    },
    {
      title: "Vendors",
      href: "#",
      icon: Users,
    },
    {
      title: "Settings",
      href: "#",
      icon: Settings,
    },
  ];

  return (
    <Card className="shadow-sm border-muted">
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3">
        {actions.map((action) => (
          <Link
            key={action.title}
            href={action.href}
            className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-transparent p-4 hover:border-primary/50 hover:bg-primary/5 transition-colors"
          >
            <action.icon className="h-5 w-5 text-muted-foreground" />
            <span className="text-xs font-medium text-center">{action.title}</span>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
