import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Combine tailwind classes safely */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Formats currency to USD or provided currency */
export function formatCurrency(amount: number | string, currency: string = "USD"): string {
  const numericAmount = typeof amount === "string" ? parseFloat(amount) : amount;
  if (isNaN(numericAmount)) return "N/A";
  
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
  }).format(numericAmount);
}

/** Formats a date string to a readable format */
export function formatDate(dateString: string | Date | undefined): string {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  if (isNaN(date.getTime())) return "N/A";
  
  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(date);
}

/** Get a status color badge class name based on state */
export function getStatusColor(status: string) {
  switch (status.toLowerCase()) {
    case "compliant":
    case "approved":
    case "success":
    case "completed":
      return "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400";
    case "partially_compliant":
    case "pending_review":
    case "pending":
      return "bg-amber-500/15 text-amber-700 dark:text-amber-400";
    case "non_compliant":
    case "rejected":
    case "failed":
    case "error":
      return "bg-red-500/15 text-red-700 dark:text-red-400";
    default:
      return "bg-slate-500/15 text-slate-700 dark:text-slate-400";
  }
}
