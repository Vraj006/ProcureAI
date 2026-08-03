"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { 
  BarChart, 
  CheckSquare, 
  FileBox, 
  Lightbulb, 
  Scale, 
  ShieldCheck,
  Users,
  FileBarChart
} from "lucide-react";

export function ProjectTabs({ workspaceId, projectId }: { workspaceId: string; projectId: string }) {
  const pathname = usePathname();
  
  const basePath = `/workspaces/${workspaceId}/projects/${projectId}`;
  
  const tabs = [
    { name: "Overview", href: basePath, icon: BarChart, exact: true },
    { name: "Vendors", href: `${basePath}/vendors`, icon: Users },
    { name: "Quotations", href: `${basePath}/quotations`, icon: FileBox },
    { name: "Analysis", href: `${basePath}/analysis`, icon: BarChart },
    { name: "Comparison", href: `${basePath}/comparison`, icon: Scale },
    { name: "Compliance", href: `${basePath}/compliance`, icon: ShieldCheck },
    { name: "Recommendation", href: `${basePath}/recommendation`, icon: Lightbulb },
    { name: "Review", href: `${basePath}/review`, icon: CheckSquare },
    { name: "Reports", href: `${basePath}/reports`, icon: FileBarChart },
  ];

  return (
    <div className="w-full border-b overflow-x-auto no-scrollbar">
      <nav className="flex space-x-1" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = tab.exact 
            ? pathname === tab.href 
            : pathname.startsWith(tab.href);
            
          return (
            <Link
              key={tab.name}
              href={tab.href}
              className={cn(
                "group inline-flex items-center whitespace-nowrap border-b-2 py-3 px-4 text-sm font-medium transition-colors",
                isActive
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:border-muted hover:text-foreground"
              )}
              aria-current={isActive ? "page" : undefined}
            >
              <tab.icon
                className={cn(
                  "mr-2 h-4 w-4",
                  isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
                )}
                aria-hidden="true"
              />
              {tab.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
