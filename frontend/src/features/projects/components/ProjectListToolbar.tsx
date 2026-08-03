import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, Plus, Filter, ArrowDownUp } from "lucide-react";

export function ProjectListToolbar() {
  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-6">
      <div className="flex flex-1 items-center gap-2 w-full max-w-sm">
        <div className="relative w-full">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input 
            placeholder="Search projects..." 
            className="pl-9 w-full bg-card shadow-sm"
          />
        </div>
      </div>
      
      <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
        <Button variant="outline" className="shadow-sm">
          <Filter className="w-4 h-4 mr-2" />
          Filter
        </Button>
        <Button variant="outline" className="shadow-sm">
          <ArrowDownUp className="w-4 h-4 mr-2" />
          Sort
        </Button>
        <Button className="ml-auto sm:ml-0 shadow-sm">
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Button>
      </div>
    </div>
  );
}
