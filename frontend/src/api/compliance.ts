import { apiFetch } from './client';

export interface BusinessProfile {
  business_type: string;
  state: string;
  county?: string | null;
  city?: string | null;
  industry: string;
  employees: number;
  annual_revenue: number;
  ownership_type: string;
  is_foreign_owner: boolean;
  is_home_based: boolean;
  additional_attributes?: Record<string, any>;
}

export interface ApplicableRule {
  rule_id: string;
  title: string;
  description: string;
  category: string;
  authority: string;
  priority: number;
  dependencies: string[];
  source: string;
}

export interface ConditionEvaluation {
  rule_id: string;
  status: 'SATISFIED' | 'FAILED' | 'PENDING_INFORMATION' | 'NOT_APPLICABLE';
  reason: string;
  missing_fields: string[];
  evaluated_conditions: Record<string, any>[];
  timestamp: string;
}

export interface EvaluationResult {
  profile: BusinessProfile;
  evaluations: ConditionEvaluation[];
  summary: Record<string, number>;
}

export interface DependencyNode {
  rule_id: string;
  title: string;
  parents: string[];
  children: string[];
  depth: number;
  status: string | null;
}

export interface DependencyGraph {
  nodes: Record<string, DependencyNode>;
  roots: string[];
  leaf_nodes: string[];
  execution_order: string[];
  cycles_detected: boolean;
}

export interface EligibilityIssue {
  rule_id: string;
  severity: 'ERROR' | 'WARNING' | 'INFO';
  message: string;
  blocking: boolean;
  recommended_action: string;
}

export interface EligibilityResult {
  status: 'ELIGIBLE' | 'CONDITIONALLY_ELIGIBLE' | 'NOT_ELIGIBLE';
  issues: EligibilityIssue[];
  blocking_rules: string[];
  missing_information: string[];
  next_steps: string[];
  summary: Record<string, any>;
}

export interface WorkflowStep {
  step_id: string;
  rule_id: string;
  title: string;
  description: string;
  status: 'NOT_STARTED' | 'AVAILABLE' | 'BLOCKED' | 'IN_PROGRESS' | 'COMPLETED';
  authority: string;
  priority: number;
  dependencies: string[];
  required_documents: string[];
  estimated_duration?: string | null;
  blocking_reason?: string | null;
}

export interface WorkflowResult {
  steps: Record<string, WorkflowStep>;
  execution_order: string[];
  critical_path: string[];
  blocked_steps: string[];
  completion_percentage: number;
  summary: Record<string, any>;
}

export interface CompliancePlan {
  profile: BusinessProfile;
  matched_rules: ApplicableRule[];
  evaluation_result: EvaluationResult;
  dependency_graph: DependencyGraph;
  eligibility_result: EligibilityResult;
  workflow_result: WorkflowResult;
  generated_at: string;
  version: string;
}

export async function generateCompliancePlan(profile: BusinessProfile): Promise<CompliancePlan> {
  return apiFetch<CompliancePlan>('/compliance/generate-plan', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
}
