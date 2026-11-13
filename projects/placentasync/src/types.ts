export enum GermLayer {
  Ectoderm = 'Ectoderm',
  Mesoderm = 'Mesoderm',
  Endoderm = 'Endoderm',
  Trophoblast = 'Trophoblast',
  Extraembryonic = 'Extraembryonic/Other',
  None = 'None',
}

export interface StructureLabel {
  id: string;
  name: string;
  color: string; // Tailwind hex or CSS color
  description: string;
  germLayer: GermLayer;
  position: [number, number, number]; // 3D coordinates for label flag
}

export interface DevelopmentalKeyPoint {
  title: string;
  description: string;
  type: 'milestone' | 'cellular' | 'morphological';
}

export interface EmbryoStage {
  id: string;
  week: number;
  day: number;
  title: string;
  subtitle: string;
  overview: string;
  keyPoints: DevelopmentalKeyPoint[];
  structures: StructureLabel[];
  educationalInsight: string;
}

export interface SlicingSettings {
  enabled: boolean;
  plane: 'sagittal' | 'transverse' | 'coronal';
  depth: number; // slider value from -1.5 to 1.5
  showCap: boolean; // whether to show a solid cap or outline at the cut
}

export interface ViewSettings {
  showLabels: boolean;
  autoRotate: boolean;
  transparentOuterLayers: boolean;
  explodedView: boolean;
  zoom: number;
}

export interface StudyNote {
  id: string;
  userId: string;
  stageId: string;
  title: string;
  content: string;
  tag?: string;
  structureId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CustomPreset {
  id: string;
  userId: string;
  stageId: string;
  name: string;
  sliceAxis: 'none' | 'x' | 'y' | 'z';
  slicePosition: number;
  explodedView: number;
  transparentOuterLayers: boolean;
  showLabels: boolean;
  autoRotate: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface StageProgress {
  id: string;
  userId: string;
  stageId: string;
  isMastered: boolean;
  quizScore: number;
  updatedAt: string;
}

export interface DiscussionPost {
  id: string;
  authorId: string;
  authorName: string;
  stageId: string;
  structureName?: string;
  content: string;
  createdAt: string;
}
