import { create } from 'zustand'

/** What the graph screen should focus on when opened from an effect card. Class and effect use our ids. */
export const useGraphFocus = create<{ cls: string | null; effect: string | null; set: (cls: string | null, effect: string | null) => void }>(set => ({
  cls: null, effect: null, set: (cls, effect) => set({ cls, effect }),
}))
