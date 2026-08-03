import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Circle, CheckCircle2, FileUp, Building2, Play } from "lucide-react";
import { cn } from "@/lib/utils";

interface TimelineEvent {
  id: string;
  type: 'project_created' | 'vendor_added' | 'quotation_uploaded' | 'analysis_started';
  title: string;
  date: string;
  isLatest?: boolean;
}

export function ActivityTimeline({ events }: { events: TimelineEvent[] }) {
  const getIcon = (type: TimelineEvent["type"]) => {
    switch (type) {
      case "project_created": return <CheckCircle2 className="h-4 w-4" />;
      case "vendor_added": return <Building2 className="h-4 w-4" />;
      case "quotation_uploaded": return <FileUp className="h-4 w-4" />;
      case "analysis_started": return <Play className="h-4 w-4" />;
      default: return <Circle className="h-4 w-4" />;
    }
  };

  const getStyle = (type: TimelineEvent["type"]) => {
    switch (type) {
      case "project_created": return "bg-emerald-100 text-emerald-600";
      case "vendor_added": return "bg-blue-100 text-blue-600";
      case "quotation_uploaded": return "bg-indigo-100 text-indigo-600";
      case "analysis_started": return "bg-purple-100 text-purple-600";
      default: return "bg-secondary text-secondary-foreground";
    }
  };

  return (
    <Card className="h-full">
      <CardHeader className="pb-4">
        <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
          <Activity className="h-4 w-4" /> Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <div className="h-full flex items-center justify-center text-sm text-muted-foreground py-12">
            No activity recorded yet
          </div>
        ) : (
          <div className="space-y-6">
            {events.map((event, index) => (
              <div key={event.id} className="relative flex gap-4">
                {/* Connector Line */}
                {index !== events.length - 1 && (
                  <div className="absolute left-4 top-8 bottom-[-24px] w-0.5 bg-border -ml-[0.5px]" />
                )}
                
                <div className={cn("relative z-10 w-8 h-8 rounded-full flex items-center justify-center shrink-0 border-2 border-background", getStyle(event.type))}>
                  {getIcon(event.type)}
                </div>
                
                <div className="flex-1 pt-1">
                  <p className={cn("text-sm transition-colors", event.isLatest ? "font-semibold text-foreground" : "font-medium text-muted-foreground")}>
                    {event.title}
                  </p>
                  <p className="text-xs text-muted-foreground mt-0.5">{event.date}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
