"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useCreateQuotation } from "@/features/quotations/api/queries";
import { useVendors } from "@/features/vendors/api/queries";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useState } from "react";

const quotationSchema = z.object({
  quotation_number: z.string().min(1, "Quotation Number is required."),
  vendor_id: z.string().uuid("Please select a valid vendor."),
});

type QuotationFormValues = z.infer<typeof quotationSchema>;

interface CreateQuotationDialogProps {
  workspaceId: string;
  projectId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateQuotationDialog({ workspaceId, projectId, open, onOpenChange }: CreateQuotationDialogProps) {
  const { mutateAsync: createQuotation, isPending } = useCreateQuotation();
  const { data: vendorsData, isLoading: vendorsLoading } = useVendors(workspaceId, undefined, 1, 100);

  const form = useForm<QuotationFormValues>({
    resolver: zodResolver(quotationSchema),
    defaultValues: {
      quotation_number: "",
      vendor_id: "",
    },
  });

  async function onSubmit(data: QuotationFormValues) {
    try {
      await createQuotation({ 
        workspaceId, 
        projectId, 
        data: {
          quotation_number: data.quotation_number,
          vendor_id: data.vendor_id
        }
      });
      form.reset();
      onOpenChange(false);
    } catch (error) {
      // Handled via toast
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add Quotation Placeholder</DialogTitle>
          <DialogDescription>
            Map a new quotation to an existing vendor. You can upload the associated PDF file later.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="vendor_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Linked Vendor</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value} disabled={isPending || vendorsLoading}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a vendor" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {vendorsData?.items.map((vendor) => (
                        <SelectItem key={vendor.id} value={vendor.id}>
                          {vendor.company_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="quotation_number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Quotation Number (Reference)</FormLabel>
                  <FormControl>
                    <Input placeholder="QT-2023-001" {...field} disabled={isPending} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            
            <DialogFooter className="pt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={isPending}>
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Create Row
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
