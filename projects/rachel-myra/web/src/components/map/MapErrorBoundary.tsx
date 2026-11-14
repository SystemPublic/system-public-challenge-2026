"use client";
// Shows a calm fallback if the browser can't draw the map (e.g. no WebGL2).
import { Component, type ReactNode } from "react";

export class MapErrorBoundary extends Component<{ children: ReactNode; height: number | string }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (this.state.failed) {
      return (
        <div style={{ height: this.props.height }} className="flex items-center justify-center bg-[var(--ui-surface,#f7f7f5)] p-4 text-center text-base text-[var(--ui-ink-muted,#4b5563)]">
          This browser can&apos;t draw the map (it needs WebGL). The directions and details are below.
        </div>
      );
    }
    return this.props.children;
  }
}
