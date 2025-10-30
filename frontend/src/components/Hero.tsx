import { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface HeroProps {
  title: string;
  subtitle?: string;
  children?: ReactNode;
  className?: string;
  size?: "default" | "large";
}

export const Hero = ({ title, subtitle, children, className, size = "default" }: HeroProps) => {
  return (
    <section className={cn("relative overflow-hidden bg-gradient-hero", className)}>
      <div className="container mx-auto px-4 py-16 md:py-24">
        <div className={cn("text-center space-y-4", size === "large" && "py-8")}>
          <h1
            className={cn(
              "font-bold text-white animate-fade-in",
              size === "large" ? "text-5xl md:text-7xl" : "text-4xl md:text-5xl"
            )}
          >
            {title}
          </h1>
          {subtitle && (
            <p className="text-lg md:text-xl text-denari-4 max-w-2xl mx-auto animate-fade-in">{subtitle}</p>
          )}
          {children && <div className="mt-8 animate-slide-up">{children}</div>}
        </div>
      </div>
    </section>
  );
};
