"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";

type StepStatus = "pending" | "completed" | "failed" | "rejected" | "approved" | "requires_changes";

interface WorkflowStep {
  id: string;
  label: string;
  status: StepStatus;
  description: string;
}

interface WorkflowTimelineProps {
  steps: WorkflowStep[];
  isGlobalLoading: boolean;
}

export function WorkflowTimeline({ steps, isGlobalLoading }: WorkflowTimelineProps) {
  const getStepIcon = (status: StepStatus) => {
    switch (status) {
      case "completed":
      case "approved":
        return <CheckCircle2 className="h-6 w-6 text-green-500" />;
      case "failed":
      case "rejected":
        return <XCircle className="h-6 w-6 text-red-500" />;
      case "requires_changes":
        return <XCircle className="h-6 w-6 text-amber-500" />;
      case "pending":
      default:
        // If the global workflow starts running, show first pending logic as running
        return <Circle className="h-6 w-6 text-muted-foreground" />;
    }
  };

  const getLineColor = (status: StepStatus, nextStatus?: StepStatus) => {
    if (status === "completed" || status === "approved") {
      return "bg-green-500";
    }
    return "bg-muted";
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    show: { opacity: 1, x: 0 },
  };

  // Find the first pending step to animate it if global loading is true
  const firstPendingIndex = steps.findIndex(s => s.status === "pending");

  return (
    <div className="w-full relative py-4">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="flex flex-col space-y-0"
      >
        {steps.map((step, index) => {
          const isLast = index === steps.length - 1;
          const isFirstPending = isGlobalLoading && index === firstPendingIndex;
          const isActive = isFirstPending;

          return (
            <motion.div key={step.id} variants={itemVariants} className="relative flex">
              {/* Timeline Connector */}
              {!isLast && (
                <div className="absolute left-3 top-8 bottom-[-16px] w-[2px]">
                  <div
                    className={cn(
                      "h-full w-full",
                      getLineColor(step.status, steps[index + 1]?.status)
                    )}
                  />
                </div>
              )}

              {/* Icon */}
              <div className="relative z-10 flex h-14 items-start justify-center pr-4">
                <div className="mt-1 bg-background rounded-full">
                  {isActive ? (
                    <Loader2 className="h-6 w-6 text-blue-500 animate-spin" />
                  ) : (
                    getStepIcon(step.status)
                  )}
                </div>
              </div>

              {/* Content */}
              <div className="pb-8 pt-1">
                <h4
                  className={cn(
                    "font-semibold text-base transition-colors",
                    isActive ? "text-blue-600" : "text-foreground"
                  )}
                >
                  {step.label}
                </h4>
                <p className="text-sm text-muted-foreground mt-1">
                  {step.description}
                </p>
                {step.status === "rejected" || step.status === "requires_changes" ? (
                  <p className="text-sm text-red-500 font-medium mt-1">Reviewer requested redesign via Human-in-the-Loop.</p>
                ) : null}
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
