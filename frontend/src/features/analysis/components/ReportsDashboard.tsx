"use client";

import { useState } from "react";
import { Download, FileText, FileSpreadsheet, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { analysisApi } from "@/services/api/analysis";
import { toast } from "sonner";

interface ReportsDashboardProps {
  workspaceId: string;
  projectId: string;
}

export function ReportsDashboard({ workspaceId, projectId }: ReportsDashboardProps) {
  const [isPdfLoading, setIsPdfLoading] = useState(false);
  const [isExcelLoading, setIsExcelLoading] = useState(false);
  const [lastGenerated, setLastGenerated] = useState<string | null>(null);

  const handleDownload = async (type: "pdf" | "excel") => {
    try {
      if (type === "pdf") setIsPdfLoading(true);
      else setIsExcelLoading(true);

      const blob = type === "pdf" 
        ? await analysisApi.downloadPdfReport(workspaceId, projectId)
        : await analysisApi.downloadExcelReport(workspaceId, projectId);

      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `procureai_executive_report_${projectId}.${type === "pdf" ? "pdf" : "xlsx"}`);
      document.body.appendChild(link);
      link.click();
      
      if (link.parentNode) link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setLastGenerated(new Date().toLocaleTimeString());
      toast.success(`${type.toUpperCase()} Report generated successfully!`);
    } catch (error) {
      toast.error(`Failed to generate ${type.toUpperCase()} report. Please ensure analysis is complete.`);
    } finally {
      if (type === "pdf") setIsPdfLoading(false);
      else setIsExcelLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight mb-2">Executive Reports</h2>
        <p className="text-muted-foreground">
          Generate professional, deterministic compliance and financial reports extracted directly from your stored AI analytics workflows.
        </p>
        
        {lastGenerated && (
          <div className="mt-4 flex items-center text-sm text-green-600 font-medium">
            <CheckCircle2 className="w-4 h-4 mr-2" />
            Last successful generation at {lastGenerated}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="flex flex-col border-primary/20 shadow-sm relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
            <FileText className="w-32 h-32 text-primary" />
          </div>
          <CardHeader>
            <CardTitle className="flex items-center text-xl">
              <FileText className="w-5 h-5 mr-2 text-primary" />
              Executive PDF Specification
            </CardTitle>
            <CardDescription>
              Comprehensive 9-page visual suite mapped dynamically. Highlights the reasoning logic, human review traces, and omission clauses natively on printed layout boundaries.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-grow">
          </CardContent>
          <CardFooter>
            <Button 
              className="w-full" 
              onClick={() => handleDownload("pdf")} 
              disabled={isPdfLoading || isExcelLoading}
            >
              {isPdfLoading ? (
                "Building ReportLab PDF..."
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" /> Download Executive PDF
                </>
              )}
            </Button>
          </CardFooter>
        </Card>

        <Card className="flex flex-col border-green-600/20 shadow-sm relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
            <FileSpreadsheet className="w-32 h-32 text-green-600" />
          </div>
          <CardHeader>
            <CardTitle className="flex items-center text-xl">
              <FileSpreadsheet className="w-5 h-5 mr-2 text-green-600" />
              Excel Financial Workbook
            </CardTitle>
            <CardDescription>
              Native .xlsx format designed specifically for procurement controllers. Encapsulates 5 distinct worksheets covering the Vendor Matrix, Quote Traces, and Cost Deductions.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-grow">
          </CardContent>
          <CardFooter>
            <Button 
              variant="outline"
              className="w-full text-green-700 hover:text-green-800 hover:bg-green-50 border-green-200" 
              onClick={() => handleDownload("excel")} 
              disabled={isPdfLoading || isExcelLoading}
            >
              {isExcelLoading ? (
                "Constructing OpenPyXL Spreadsheet..."
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" /> Download Excel Report
                </>
              )}
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
