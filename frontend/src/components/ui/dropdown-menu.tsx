"use client";

import { Fragment, HTMLAttributes, forwardRef, useRef, useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { X, ChevronRight, Check } from "lucide-react";

interface DropdownMenuProps extends HTMLAttributes<HTMLDivElement> {}

export const DropdownMenu = forwardRef<HTMLDivElement, DropdownMenuProps>(
  ({ className, children, ...props }, ref) => {
    const [open, setOpen] = useState(false);
    const triggerRef = useRef<HTMLButtonElement>(null);
    const contentRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      function handleClickOutside(event: MouseEvent) {
        if (
          contentRef.current &&
          !contentRef.current.contains(event.target as Node) &&
          triggerRef.current &&
          !triggerRef.current.contains(event.target as Node)
        ) {
          setOpen(false);
        }
      }

      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
      <div ref={ref} className={cn("relative inline-block", className)} {...props}>
        <button
          ref={triggerRef}
          onClick={() => setOpen(!open)}
          className="inline-flex items-center gap-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring"
        >
          {React.Children.map(children, (child) => {
            if (React.isValidElement(child) && child.type === DropdownMenuTrigger) {
              return React.cloneElement(child, { onClick: () => setOpen(!open) });
            }
            return child;
          })}
        </button>

        {open && (
          <div
            ref={contentRef}
            className="absolute right-0 z-50 mt-2 w-56 origin-top-right rounded-md bg-popover p-1 text-popover-foreground shadow-lg ring-1 ring-border animate-slide-down"
            role="menu"
          >
            {React.Children.map(children, (child) => {
              if (React.isValidElement(child) && child.type === DropdownMenuContent) {
                return React.cloneElement(child, {});
              }
              return child;
            })}
          </div>
        )}
      </div>
    );
  }
);

DropdownMenu.displayName = "DropdownMenu";

interface DropdownMenuTriggerProps extends HTMLAttributes<HTMLButtonElement> {}

export const DropdownMenuTrigger = forwardRef<HTMLButtonElement, DropdownMenuTriggerProps>(
  ({ className, children, ...props }, ref) => (
    <button ref={ref} className={cn("", className)} {...props}>
      {children}
    </button>
  )
);

DropdownMenuTrigger.displayName = "DropdownMenuTrigger";

interface DropdownMenuContentProps extends HTMLAttributes<HTMLDivElement> {}

export const DropdownMenuContent = forwardRef<HTMLDivElement, DropdownMenuContentProps>(
  ({ className, children, ...props }, ref) => (
    <div ref={ref} className={cn("", className)} {...props}>
      {children}
    </div>
  )
);

DropdownMenuContent.displayName = "DropdownMenuContent";

interface DropdownMenuItemProps extends HTMLAttributes<HTMLButtonElement> {
  inset?: boolean;
  shortcut?: string;
  checked?: boolean;
}

export const DropdownMenuItem = forwardRef<HTMLButtonElement, DropdownMenuItemProps>(
  ({ className, inset, shortcut, checked, children, onClick, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(
        "relative flex w-full cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        inset && "pl-8",
        className
      )}
      onClick={(e) => {
        onClick?.(e);
        const menu = e.currentTarget.closest("[role='menu']");
        if (menu) {
          // Find parent DropdownMenu and close
          const trigger = menu.previousElementSibling?.querySelector("button");
          if (trigger) {
            (trigger as HTMLButtonElement).click();
          }
        }
      }}
      {...props}
    >
      {checked && <Check className="mr-2 h-4 w-4" />}
      {children}
      {shortcut && (
        <span className="ml-auto text-xs tracking-widest opacity-60">{shortcut}</span>
      )}
    </button>
  )
);

DropdownMenuItem.displayName = "DropdownMenuItem";

interface DropdownMenuSeparatorProps extends HTMLAttributes<HTMLDivElement> {}

export const DropdownMenuSeparator = forwardRef<HTMLDivElement, DropdownMenuSeparatorProps>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("-mx-1 my-1 h-px bg-muted", className)}
      {...props}
    />
  )
);

DropdownMenuSeparator.displayName = "DropdownMenuSeparator";

interface DropdownMenuLabelProps extends HTMLAttributes<HTMLDivElement> {
  inset?: boolean;
}

export const DropdownMenuLabel = forwardRef<HTMLDivElement, DropdownMenuLabelProps>(
  ({ className, inset, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("px-2 py-1.5 text-sm font-semibold", inset && "pl-8", className)}
      {...props}
    />
  )
);

DropdownMenuLabel.displayName = "DropdownMenuLabel";