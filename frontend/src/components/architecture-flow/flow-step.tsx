"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import type { LucideIcon } from "lucide-react";

type FlowStepProps = {
  stepNumber: number;
  title: string;
  subtitle: string;
  icon: LucideIcon;
  accentClass?: string;
  children: React.ReactNode;
  isLast?: boolean;
};

export function FlowStep({
  stepNumber,
  title,
  subtitle,
  icon: Icon,
  accentClass = "bg-primary/10 text-primary ring-primary/20",
  children,
  isLast = false,
}: FlowStepProps): React.JSX.Element {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <div ref={ref} className="relative">
      {/* Connector line */}
      {!isLast && (
        <div className="absolute left-6 top-16 bottom-0 w-px sm:left-8">
          <motion.div
            className="h-full w-full bg-gradient-to-b from-border via-border/60 to-transparent"
            initial={{ scaleY: 0 }}
            animate={isInView ? { scaleY: 1 } : { scaleY: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            style={{ transformOrigin: "top" }}
          />
        </div>
      )}

      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -20 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className="relative flex gap-4 pb-12 sm:gap-6"
      >
        {/* Step badge */}
        <div className="relative z-10 flex flex-col items-center">
          <div
            className={`flex size-12 shrink-0 items-center justify-center rounded-2xl ring-1 sm:size-16 ${accentClass}`}
          >
            <Icon className="size-5 sm:size-6" />
          </div>
          <span className="mt-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            Step {stepNumber}
          </span>
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1 pt-1">
          <h3 className="text-lg font-semibold text-foreground sm:text-xl">{title}</h3>
          <p className="mt-0.5 text-sm text-muted-foreground">{subtitle}</p>
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 12 }}
            transition={{ duration: 0.4, delay: 0.2 }}
            className="mt-4"
          >
            {children}
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
}
