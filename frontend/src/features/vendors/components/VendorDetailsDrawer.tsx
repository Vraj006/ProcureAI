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

        <div className="space-y-6">
          {/* Identity Info */}
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">Identity</h4>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm">
                <Hash className="w-4 h-4 text-muted-foreground" />
                <span className="font-medium text-foreground">GST/Tax:</span>
                <span className="text-muted-foreground">{vendor.tax_number || "Not provided"}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Building className="w-4 h-4 text-muted-foreground" />
                <span className="font-medium text-foreground">Address:</span>
                <span className="text-muted-foreground">{vendor.address || "Not provided"}</span>
              </div>
            </div>
          </div>

          <Separator />

          {/* Contact Info */}
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">Primary Contact</h4>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm">
                <span className="font-medium text-foreground ml-7">{vendor.contact_person || "No name provided"}</span>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Mail className="w-4 h-4 text-muted-foreground" />
                {vendor.email ? (
                  <a href={`mailto:${vendor.email}`} className="text-primary hover:underline">{vendor.email}</a>
                ) : (
                  <span className="text-muted-foreground">Not provided</span>
                )}
              </div>
              <div className="flex items-center gap-3 text-sm">
                <Phone className="w-4 h-4 text-muted-foreground" />
                {vendor.phone ? (
                  <a href={`tel:${vendor.phone}`} className="text-primary hover:underline">{vendor.phone}</a>
                ) : (
                  <span className="text-muted-foreground">Not provided</span>
                )}
              </div>
            </div>
          </div>

          <Separator />
          
          {/* System Info */}
          <div>
            <h4 className="text-sm font-medium text-muted-foreground mb-3">System Metrics</h4>
            <div className="space-y-3">
              <div className="flex items-center gap-3 text-sm">
                <Calendar className="w-4 h-4 text-muted-foreground" />
                <span className="font-medium text-foreground">Added On:</span>
                <span className="text-muted-foreground">{new Date(vendor.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="pt-6 flex gap-3">
            <Button className="w-full" onClick={() => {
              onOpenChange(false);
              setTimeout(onEditClick, 200);
            }}>
              Edit Vendor
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
