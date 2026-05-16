export type ClaimType =
  | 'fact'
  | 'number'
  | 'comparison'
  | 'causality'
  | 'generalization'
  | 'opinion'
  | 'definition'
  | 'unsupported_conclusion';

export type EvidenceStatus =
  | 'supported_by_text'
  | 'needs_source'
  | 'weak_argument'
  | 'too_strong'
  | 'unverifiable_from_text'
  | 'ok';

export type RiskLevel = 'low' | 'medium' | 'high';

export interface StructureAnalysis {
  main_idea: string;
  goal: string;
  target_audience: string;
  structure_summary: string;
  logic_quality_score: number;
  clarity_score: number;
  problems: string[];
  suggestions: string[];
}

export interface Claim {
  id: string;
  text: string;
  claim_type: ClaimType;
  location: string;
  needs_evidence: boolean;
  evidence_status: EvidenceStatus;
  risk_level: RiskLevel;
  explanation: string;
  recommendation: string;
  suggested_rewrite: string;
}

export interface AudienceQuestion {
  id: string;
  question: string;
  asked_by: string;
  category: string;
  why_asked: string;
  risk_level: RiskLevel;
  suggested_answer: string;
  how_to_improve_material: string;
}

export interface Recommendation {
  id: string;
  priority: RiskLevel;
  category: string;
  problem: string;
  action: string;
  expected_effect: string;
}

export interface ImprovementPlan {
  quick_fixes_30_min: string[];
  improvements_2_hours: string[];
  final_polish: string[];
}

export interface Weakness {
  problem: string;
  why_problem: string;
  audience_signal: string;
  fix: string;
}

export interface ScoringBreakdown {
  clarity_score: number;
  structure_score: number;
  argument_score: number;
  evidence_score: number;
  audience_score: number;
  question_readiness_score: number;
  explanation: string;
}

export interface StressTest {
  most_dangerous_question: string;
  why_dangerous: string;
  exposed_weakness: string;
  suggested_answer: string;
  what_to_add: string;
}

export interface AnalysisResult {
  id: string;
  filename: string;
  material_type: string;
  audience_type: string;
  provider_name: string;
  provider_model: string;
  provider_response_id: string | null;
  is_mock: boolean;
  title: string;
  created_at: string;
  persuasiveness_score: number;
  scoring_breakdown: ScoringBreakdown;
  summary: string;
  main_idea: string;
  strengths: string[];
  weaknesses: Weakness[];
  risks: string[];
  warnings: string[];
  structure_analysis: StructureAnalysis;
  claims: Claim[];
  recommendations: Recommendation[];
  audience_questions: AudienceQuestion[];
  improvement_plan: ImprovementPlan;
  stress_test: StressTest;
}

export interface AnalysisCreateResponse {
  analysis_id: string;
  status: 'completed';
  result: AnalysisResult;
}

export interface AnalysisSummary {
  id: string;
  filename: string;
  material_type: string;
  audience_type: string;
  persuasiveness_score: number;
  provider_name: string | null;
  is_mock: boolean;
  created_at: string;
}

export interface ReportResponse {
  analysis_id: string;
  markdown: string;
}
