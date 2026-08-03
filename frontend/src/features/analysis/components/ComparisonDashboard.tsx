"use client";

import { useComparison } from "../hooks/useAnalysisQueries";
import { useVendors } from "@/features/vendors/api/queries";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Trophy, Clock, Shield, DollarSign, Scale, FileWarning } from "lucide-react";
import { motion } from "framer-motion";

interface ComparisonDashboardProps {
  workspaceId: string;
  projectId: string;
}

export function ComparisonDashboard({ workspaceId, projectId }: ComparisonDashboardProps) {
  const { data: comparisonResponse, isLoading, error } = useComparison(workspaceId, projectId);
  const { data: vendorsData } = useVendors(workspaceId, undefined, 1, 100);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32 w-full rounded-xl" />
          <Skeleton className="h-32 w-full rounded-xl" />
          <Skeleton className="h-32 w-full rounded-xl" />
        </div>
        <Skeleton className="h-[400px] w-full rounded-xl" />
      </div>
    );
  }

  if (error || !comparisonResponse?.success) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg border-dashed bg-secondary/10 shadow-sm mt-4">
        <div className="h-16 w-16 bg-muted rounded-full flex items-center justify-center mb-6">
          <FileWarning className="h-8 w-8 text-muted-foreground" />
        </div>
        <h3 className="text-xl font-bold tracking-tight mb-2">Comparison Data Unavailable</h3>
        <p className="text-muted-foreground max-w-sm text-sm">
          {error?.message || comparisonResponse?.errors?.[0] || "No comparative data was generated. Ensure analysis has been run on extracted quotes."}
        </p>
      </div>
    );
  }

  const { data } = comparisonResponse;
  
  const rankings = data.vendor_rankings || [];
  
  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 mb-2">
        <Scale className="h-6 w-6 text-primary" />
        <h2 className="text-2xl font-bold tracking-tight">Vendor Metric Comparison</h2>
      </div>
      
      {/* Executive Summary Cards */}
      <motion.div 
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        <motion.div variants={item}>
          <Card className="bg-gradient-to-br from-background to-emerald-500/10 border-emerald-500/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-emerald-600 flex items-center gap-2">
                <DollarSign className="h-4 w-4" /> Lowest Price
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold truncate" title={data.lowest_price_vendor || "None"}>
                {data.lowest_price_vendor || "None"}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Cost optimized baseline</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={item}>
          <Card className="bg-gradient-to-br from-background to-blue-500/10 border-blue-500/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-blue-600 flex items-center gap-2">
                <Clock className="h-4 w-4" /> Fastest Delivery
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold truncate" title={data.fastest_delivery_vendor || "None"}>
                {data.fastest_delivery_vendor || "None"}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Shortest lead time evaluation</p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={item}>
          <Card className="bg-gradient-to-br from-background to-purple-500/10 border-purple-500/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-purple-600 flex items-center gap-2">
                <Shield className="h-4 w-4" /> Best Warranty
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold truncate" title={data.best_warranty_vendor || "None"}>
                {data.best_warranty_vendor || "None"}
              </div>
              <p className="text-xs text-muted-foreground mt-1">Extensive coverage matrix</p>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>

      {/* Vendor Rankings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-amber-500" />
            Overall Rankings
          </CardTitle>
          <CardDescription>Aggregate algorithmic scoring based on normalized price, term constraints, and delivery logic.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[100px]">Rank</TableHead>
                <TableHead>Vendor Name</TableHead>
                <TableHead>Grand Total</TableHead>
                <TableHead>Delivery & Terms</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rankings.map((rankedItem: any, idx: number) => (
                <TableRow key={idx}>
                  <TableCell className="font-semibold px-4">
                    {rankedItem.rank === 1 ? (
                       <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-100 shadow-none border-0 px-2 py-0.5">#1 Best</Badge>
                    ) : (
                       `#${rankedItem.rank}`
                    )}
                  </TableCell>
                  <TableCell className="font-medium">{rankedItem.vendor_name || "Unknown Vendor"}</TableCell>
                  <TableCell className="font-mono text-sm">
                    {rankedItem.grand_total ? `${data.currency || '$'} ${rankedItem.grand_total.toLocaleString()}` : "N/A"}
                  </TableCell>
                  <TableCell className="text-muted-foreground text-sm space-y-1">
                    <div><span className="font-medium">Discount:</span> {rankedItem.discount ? `${rankedItem.discount}%` : "None"}</div>
                    <div><span className="font-medium">Delivery:</span> {rankedItem.delivery_time || "N/A"}</div>
                    <div><span className="font-medium">Warranty:</span> {rankedItem.warranty || "N/A"}</div>
                  </TableCell>
                </TableRow>
              ))}
              {rankings.length === 0 && (
                <TableRow>
                  <TableCell colSpan={4} className="h-24 text-center text-muted-foreground">
                    No vendors ranked.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
