/**
 * Utility functions for styling and DOM operations.
 *
 * Provides helper functions for combining and merging Tailwind CSS class names,
 * particularly useful for conditional and dynamic styling in components.
 *
 * @module lib/utils
 */

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

/**
 * Combines multiple class names with smart merging of Tailwind utilities.
 *
 * Handles conflicting Tailwind CSS utilities by removing duplicates
 * and properly applying specificity. Useful for conditional styling.
 *
 * @example
 * cn("px-2", "px-4") // Returns 'px-4' (latest specificity wins)
 * cn("text-red-500", { "text-blue-500": isActive })
 *
 * @param {...ClassValue[]} inputs - Class names, objects, or arrays to merge
 * @returns {string} Merged and deduplicated class string
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
