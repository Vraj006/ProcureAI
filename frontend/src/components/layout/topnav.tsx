import { useAuth } from "@/providers/auth-provider";
import { LogOut, Bell, Search, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function TopNav() {
  const { logout } = useAuth();

  return (
    <header className="h-16 flex-shrink-0 border-b border-border bg-card px-4 md:px-6 flex items-center justify-between">
      {/* Mobile Menu (Hidden on desktop) */}
      <div className="flex md:hidden items-center">
        <Button variant="ghost" size="icon" className="mr-2">
          <Menu className="w-5 h-5" />
        </Button>
        <span className="font-semibold text-lg tracking-tight">ProcureAI</span>
      </div>

      {/* Search Bar - Desktop View */}
      <div className="hidden md:flex flex-1 max-w-md">
        <div className="relative w-full">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search projects, vendors..."
            className="w-full bg-secondary/50 border-none pl-9 shadow-inner focus-visible:ring-primary"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 md:gap-4 ml-auto">
        <Button variant="ghost" size="icon" className="relative text-muted-foreground hover:text-foreground">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full border border-card" />
        </Button>
        
        <div className="w-px h-6 bg-border mx-1" />
        
        <Button variant="ghost" size="sm" onClick={logout} className="text-muted-foreground hover:text-destructive gap-2">
          <LogOut className="w-4 h-4" />
          <span className="hidden md:inline">Log out</span>
        </Button>
      </div>
    </header>
  );
}
