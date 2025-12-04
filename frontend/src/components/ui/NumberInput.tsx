import React from "react";
import { Input } from "./input";

interface NumberInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  // All standard input props are inherited
}

/**
 * NumberInput component that prevents mouse wheel from changing values
 * Use this instead of regular Input for type="number" fields
 */
export const NumberInput = React.forwardRef<HTMLInputElement, NumberInputProps>(
  ({ onWheel, ...props }, ref) => {
    const handleWheel = (e: React.WheelEvent<HTMLInputElement>) => {
      // Prevent mouse wheel from changing the value
      e.currentTarget.blur();
      if (onWheel) {
        onWheel(e);
      }
    };

    return <Input {...props} ref={ref} onWheel={handleWheel} />;
  }
);

NumberInput.displayName = "NumberInput";

