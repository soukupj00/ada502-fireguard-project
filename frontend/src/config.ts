/**
 * Project metadata and configuration constants.
 *
 * Contains information about the FireGuard project, including author details,
 * license information, and academic context.
 *
 * @module config
 */

/**
 * Project configuration object containing metadata.
 *
 * @property {string[]} authors - List of project authors
 * @property {string} license - Project license type
 * @property {Object} university - University and course information
 * @property {string} university.name - Full name of the university
 * @property {string} university.city - University location
 * @property {string} university.course - Academic course code and name
 */
export const projectConfig = {
  authors: ["Jan Soukup", "Nora Lehmann"],
  license: "MIT License",
  university: {
    name: "Western Norway University of Applied Sciences (HVL)",
    city: "Bergen",
    course: "ADA502 Cloud Computing",
  },
}
