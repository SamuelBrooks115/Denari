import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  className?: string;
  align?: "left" | "center";
}

export const SectionHeader = ({
  title,
  subtitle,
  children,
  className,
  align = "center",
}: SectionHeaderProps) => {
  return (
    <div className={cn("space-y-3", align === "center" && "text-center", className)}>
      <h2 className="text-3xl md:text-4xl font-bold text-denari-1">{title}</h2>
      {subtitle && <p className="text-lg text-muted-foreground max-w-2xl mx-auto">{subtitle}</p>}
      {children}
    </div>
  );
};
