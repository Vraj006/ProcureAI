"use client";

import { VendorResponse } from "@/services/api/types";
import { Button } from "@/components/ui/button";
import { Mail, Phone, Building, ExternalLink, Calendar, Hash } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";

interface VendorDetailsDrawerProps {
  vendor: VendorResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onEditClick: () => void;
}

export function VendorDetailsDrawer({ vendor, open, onOpenChange, onEditClick }: VendorDetailsDrawerProps) {
  if (!vendor) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="overflow-y-auto w-full sm:max-w-md">
        <SheetHeader className="pb-6">
          <SheetTitle className="text-2xl">{vendor.company_name}</SheetTitle>
          <SheetDescription>
            ID: {vendor.id}
          </SheetDescription>
        </SheetHeader>

          <div className="space-y-6 flex-1 px-1">
          {/* Identity Info */}
          <div className="bg-card border rounded-xl overflow-hidden shadow-sm">
            <div className="bg-muted/50 px-4 py-3 border-b flex items-center justify-between">
              <h4 className="text-sm font-semibold tracking-tight">Identity Details</h4>
              <Building className="w-4 h-4 text-muted-foreground/70" />
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-[24px_1fr] items-start gap-2 text-sm">
                <Hash className="w-4 h-4 text-primary mt-0.5" />
                <div>
                  <span className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">GST/Tax Registration</span>
                  <span className="font-medium text-foreground">{vendor.tax_number || "Not Available"}</span>
                </div>
              </div>
              <div className="grid grid-cols-[24px_1fr] items-start gap-2 text-sm">
                <Building className="w-4 h-4 text-primary mt-0.5" />
                <div>
                  <span className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">Corporate Address</span>
                  <span className="font-medium text-foreground">{vendor.address || "No address provided"}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Contact Info */}
          <div className="bg-card border rounded-xl overflow-hidden shadow-sm">
            <div className="bg-muted/50 px-4 py-3 border-b flex items-center justify-between">
              <h4 className="text-sm font-semibold tracking-tight">Primary Contact</h4>
              <Phone className="w-4 h-4 text-muted-foreground/70" />
            </div>
            <div className="p-4 space-y-4">
              <div className="grid grid-cols-[24px_1fr] items-start gap-2 text-sm">
                <span className="w-4 h-4 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[9px] font-bold mt-0.5 uppercase">
                  {vendor.contact_person ? vendor.contact_person[0] : "?"}
                </span>
                <div>
                  <span className="block text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">Point of Contact</span>
                  <span className="font-medium text-foreground">{vendor.contact_person || "Unassigned"}</span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="space-y-1.5 p-3 rounded-lg border bg-muted/10">
                  <div className="flex items-center text-xs text-muted-foreground font-medium">
                    <Mail className="w-3.5 h-3.5 mr-1.5" /> Email Address
                  </div>
                  <div className="text-sm font-medium truncate">
                    {vendor.email ? (
                      <a href={`mailto:${vendor.email}`} className="text-blue-600 hover:underline">{vendor.email}</a>
                    ) : (
                      <span className="text-muted-foreground/50">Unknown</span>
                    )}
                  </div>
                </div>
                
                <div className="space-y-1.5 p-3 rounded-lg border bg-muted/10">
                  <div className="flex items-center text-xs text-muted-foreground font-medium">
                    <Phone className="w-3.5 h-3.5 mr-1.5" /> Phone Number
                  </div>
                  <div className="text-sm font-medium truncate">
                    {vendor.phone ? (
                      <a href={`tel:${vendor.phone}`} className="text-blue-600 hover:underline">{vendor.phone}</a>
                    ) : (
                      <span className="text-muted-foreground/50">Unknown</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* System Info */}
          <div className="bg-card border rounded-xl overflow-hidden shadow-sm">
            <div className="p-4 flex items-center justify-between text-sm">
              <div className="flex items-center text-muted-foreground">
                <Calendar className="w-4 h-4 mr-2" />
                <span className="font-medium">Registered Date</span>
              </div>
              <span className="font-medium text-foreground">{new Date(vendor.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}</span>
            </div>
          </div>
        </div>

        {/* Footer overlay */}
        <div className="mt-8 border-t pt-4 bg-background">
          <Button size="lg" className="w-full shadow-sm" onClick={() => {
            onEditClick();
            setTimeout(() => onOpenChange(false), 50);
          }}>
            Edit Vendor Profile
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
