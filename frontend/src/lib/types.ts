export type Evidence = {
  evidence_id: string;
  transcript_id: string;
  expert: string;
  role: string;
  market: string;
  timestamp: string;
  quote: string;
};

export type TranscriptSummary = {
  transcript_id: string;
  expert: string;
  role: string;
  market: string;
  segment_count: number;
  evidence_count: number;
};

export type Corpus = {
  expert_count: number;
  evidence_count: number;
  transcript_count: number;
  guide_question_count: number;
  provider: string;
  transcripts: TranscriptSummary[];
};

export type Segment = {
  segment_id: string;
  speaker: string;
  timestamp: string | null;
  timestamp_display: string;
  text: string;
};

export type TranscriptDetail = TranscriptSummary & {
  segments: Segment[];
};

export type GuideQuestion = {
  number: number;
  text: string;
};

export type Guide = {
  title: string;
  objective: string;
  questions: GuideQuestion[];
};

export type GuideQuestionResult = {
  number: number;
  question: string;
  answer: string;
  evidence: Evidence[];
  coverage: { expert: string; market: string; evidence_ids: string[] }[];
  coverage_label: string;
  experts_covered: number;
  experts_total: number;
};

export type GuideReport = {
  title: string;
  objective: string;
  questions: GuideQuestionResult[];
};

export type Theme = {
  name: string;
  summary: string;
  coverage_label: string;
  single_expert: boolean;
  supporting: Evidence[];
  conflicting: Evidence[];
};

export type Difference = {
  topic: string;
  summary: string;
  positions: {
    expert: string;
    market: string;
    scope: string | null;
    evidence: Evidence[];
  }[];
};

export type QAResponse = {
  answer: string;
  evidence: Evidence[];
};
