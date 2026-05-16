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
export type RegulationRequirementStatus = 'met' | 'missing' | 'partially_met' | 'unverifiable';
export type BenchmarkGapLevel = 'low' | 'medium' | 'high';
export type ReadinessVerdict = 'ready' | 'almost_ready' | 'needs_work';
export type ConfidenceLevel = 'low' | 'medium' | 'high';

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

export interface EventRegulation {
  id: string;
  filename: string;
  raw_text: string;
  extracted_summary: string;
  event_name: string | null;
  work_format: string | null;
  evaluation_criteria: string[];
  required_sections: string[];
  forbidden_items: string[];
  formatting_requirements: string[];
  deadlines: string[];
  audience_expectations: string[];
  unknown_requirements: string[];
}

export interface RegulationCheckItem {
  requirement: string;
  status: RegulationRequirementStatus;
  evidence_from_material: string;
  risk_level: RiskLevel;
  recommendation: string;
}

export interface RegulationAnalysis {
  summary: string;
  matched_requirements: string[];
  missing_requirements: string[];
  high_risk_requirements: string[];
  checklist: RegulationCheckItem[];
  event_regulation: EventRegulation | null;
}

export interface BenchmarkWork {
  id: string;
  filename: string;
  raw_text: string;
  summary: string;
  structure_analysis: string;
  strengths: string[];
  reusable_patterns: string[];
  warnings: string[];
}

export interface ComparisonItem {
  aspect: string;
  user_material_observation: string;
  benchmark_observation: string;
  gap_level: BenchmarkGapLevel;
  recommendation: string;
}

export interface BenchmarkComparison {
  summary: string;
  what_user_material_does_better: string[];
  what_benchmark_does_better: string[];
  missing_elements: string[];
  structure_gap: ComparisonItem;
  evidence_gap: ComparisonItem;
  clarity_gap: ComparisonItem;
  action_items: string[];
  do_not_copy_warning: string;
  comparison_items: ComparisonItem[];
  benchmark_work: BenchmarkWork | null;
}

export interface OverthinkingGuard {
  readiness_verdict: ReadinessVerdict;
  confidence_level: ConfidenceLevel;
  critical_fixes: string[];
  optional_improvements: string[];
  safe_to_ignore: string[];
  stop_doing_list: string[];
  next_best_three_actions: string[];
  timeboxed_plan: Record<string, string[]>;
  reassuring_summary: string;
  when_to_stop: string;
}

export interface AnalysisResult {
  id: string;
  filename: string;
  material_type: string;
  audience_type: string;
  audience_knowledge_level: number;
  audience_knowledge_label: string;
  audience_adaptation_notes: string[];
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
  regulation_analysis: RegulationAnalysis | null;
  benchmark_comparison: BenchmarkComparison | null;
  overthinking_guard: OverthinkingGuard;
}

export interface UploadAnalysisPayload {
  file: File;
  materialType: string;
  audienceType: string;
  audienceKnowledgeLevel: number;
  regulationFile?: File | null;
  benchmarkFile?: File | null;
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
  audience_knowledge_level: number;
  has_regulation: boolean;
  has_benchmark: boolean;
  readiness_verdict: ReadinessVerdict | null;
  persuasiveness_score: number;
  provider_name: string | null;
  is_mock: boolean;
  created_at: string;
}

export interface ReportResponse {
  analysis_id: string;
  markdown: string;
}
