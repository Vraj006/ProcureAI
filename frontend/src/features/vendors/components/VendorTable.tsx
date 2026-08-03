import { VendorResponse } from "@/services/api/types";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { buttonVariants } from "@/components/ui/button";
import { MoreHorizontal, Eye, Edit, Trash, FileText } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface VendorTableProps {
  vendors: VendorResponse[];
  onView: (vendor: VendorResponse) => void;
  onEdit: (vendor: VendorResponse) => void;
  onDelete: (vendor: VendorResponse) => void;
}

export function VendorTable({ vendors, onView, onEdit, onDelete }: VendorTableProps) {
  return (
    <div className="rounded-md border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Company</TableHead>
            <TableHead>Contact</TableHead>
            <TableHead>Email</TableHead>
            <TableHead>Phone</TableHead>
            <TableHead>GST/Tax ID</TableHead>
            <TableHead className="w-[80px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {vendors.map((vendor) => (
            <TableRow key={vendor.id}>
              <TableCell className="font-medium">
                {vendor.company_name}
              </TableCell>
              <TableCell>{vendor.contact_person || "-"}</TableCell>
              <TableCell>{vendor.email || "-"}</TableCell>
              <TableCell>{vendor.phone || "-"}</TableCell>
              <TableCell>
                {vendor.tax_number ? (
                  <Badge variant="outline">{vendor.tax_number}</Badge>
                ) : (
                  "-"
                )}
              </TableCell>
              <TableCell>
                <DropdownMenu>
                  <DropdownMenuTrigger className={buttonVariants({ variant: "ghost", className: "h-8 w-8 p-0" })}>
                    <span className="sr-only">Open menu</span>
                    <MoreHorizontal className="h-4 w-4 text-muted-foreground" />
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onView(vendor)}>
                      <Eye className="mr-2 h-4 w-4" /> View Details
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => onEdit(vendor)}>
                      <Edit className="mr-2 h-4 w-4" /> Edit Vendor
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem 
                      onClick={() => onDelete(vendor)}
                      className="text-destructive focus:text-destructive focus:bg-destructive/10"
                    >
                      <Trash className="mr-2 h-4 w-4" /> Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
