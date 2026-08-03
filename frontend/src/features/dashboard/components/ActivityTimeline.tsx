import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, AlertCircle, Clock, FileText } from "lucide-react";

const mockTimeline = [
  { id: 1, title: "Recommendation Approved", project: "Q3 IT Hardware", time: "2 hours ago", icon: CheckCircle2, color: "text-emerald-500" },
  { id: 2, title: "Compliance Check Failed", project: "Office Furniture", time: "5 hours ago", icon: AlertCircle, color: "text-red-500" },
  { id: 3, title: "Pending Human Review", project: "Cloud Infrastructure Setup", time: "1 day ago", icon: Clock, color: "text-amber-500" },
  { id: 4, title: "New Quotation Uploaded", project: "Marketing Agency RFP", time: "2 days ago", icon: FileText, color: "text-blue-500" },
];

export function ActivityTimeline() {
  return (
    <Card className="shadow-sm h-full">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-8">
          {mockTimeline.map((item, index) => (
            <div key={item.id} className="relative flex gap-4">
              {/* Timeline line connecting items */}
              {index !== mockTimeline.length - 1 && (
                <div className="absolute left-4 top-8 bottom-[-24px] w-px bg-border" />
              )}
              <div className={`relative z-10 flex h-8 w-8 items-center justify-center rounded-full bg-secondary ring-8 ring-card ${item.color}`}>
                <item.icon className="h-4 w-4" />
              </div>
              <div className="flex flex-col pt-1">
                <span className="text-sm font-medium">{item.title}</span>
                <span className="text-sm text-foreground/80">{item.project}</span>
                <span className="text-xs text-muted-foreground mt-0.5">{item.time}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
