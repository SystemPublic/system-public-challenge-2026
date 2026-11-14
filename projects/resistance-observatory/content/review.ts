/**
 * Review flag carried by science content. Everything shipped is
 * `reviewed: true`; there is no on-screen "held" state any more. Content that
 * has not been written from a project doc is left out rather than held.
 */
export type Reviewable<T> = { value: T; reviewed: boolean };
