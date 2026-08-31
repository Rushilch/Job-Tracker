export interface Tag {
  id: string;
  name: string;
  color: string;
  created_at: string;
}

export interface TagCreate {
  name: string;
  color?: string;
}

export interface ResourceLink {
  label: string;
  url: string;
}

export interface SolutionEntry {
  label: string;
  code: string;
  language: string;
  explanation: string;
  time_complexity: string;
  space_complexity: string;
  tags: string[];
}

export interface Question {
  id: string;
  title: string;
  description: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  topic: string;
  application_id?: string | null;
  company?: string | null;
  role?: string | null;
  solutions: SolutionEntry[];
  links: ResourceLink[];
  tags: string[];
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface QuestionCreate {
  title: string;
  description?: string;
  difficulty?: 'Easy' | 'Medium' | 'Hard';
  topic?: string;
  application_id?: string | null;
  company?: string | null;
  role?: string | null;
  solutions?: SolutionEntry[];
  links?: ResourceLink[];
  tags?: string[];
  notes?: string;
}

export interface QuestionUpdate {
  title?: string;
  description?: string;
  difficulty?: 'Easy' | 'Medium' | 'Hard';
  topic?: string;
  application_id?: string | null;
  company?: string | null;
  role?: string | null;
  solutions?: SolutionEntry[];
  links?: ResourceLink[];
  tags?: string[];
  notes?: string;
}

export interface InterviewQA {
  question: string;
  answer: string;
  category: 'Technical' | 'Behavioral' | 'System Design' | 'Other';
  links: ResourceLink[];
}

export interface InterviewProcessStep {
  round_number: number;
  round_type: string; // 'OA', 'TA', 'BA', 'SD', 'HR', 'HM', or custom
  description: string;
}

export interface Experience {
  id: string;
  company: string;
  role: string;
  application_id?: string | null;
  date?: string | null;
  interview_process: InterviewProcessStep[];
  questions_asked: InterviewQA[];
  rating: number; // 1 - 10
  overall_notes: string;
  links: ResourceLink[];
  tags: string[];
  outcome?: string;
  created_at: string;
  updated_at: string;
}

export interface ExperienceCreate {
  company: string;
  role?: string;
  application_id?: string | null;
  date?: string | null;
  interview_process?: InterviewProcessStep[];
  questions_asked?: InterviewQA[];
  rating?: number;
  overall_notes?: string;
  links?: ResourceLink[];
  tags?: string[];
  outcome?: string;
}

export interface ExperienceUpdate {
  company?: string;
  role?: string;
  application_id?: string | null;
  date?: string | null;
  interview_process?: InterviewProcessStep[];
  questions_asked?: InterviewQA[];
  rating?: number;
  overall_notes?: string;
  links?: ResourceLink[];
  tags?: string[];
  outcome?: string;
}

export interface FlashCard {
  id: string;
  front: string;
  back: string;
  application_id?: string | null;
  company?: string | null;
  tags: string[];
  links: ResourceLink[];
  difficulty: 'Easy' | 'Medium' | 'Hard';
  created_at: string;
  updated_at: string;
}

export interface FlashCardCreate {
  front: string;
  back: string;
  application_id?: string | null;
  company?: string | null;
  tags?: string[];
  links?: ResourceLink[];
  difficulty?: 'Easy' | 'Medium' | 'Hard';
}

export interface FlashCardUpdate {
  front?: string;
  back?: string;
  application_id?: string | null;
  company?: string | null;
  tags?: string[];
  links?: ResourceLink[];
  difficulty?: 'Easy' | 'Medium' | 'Hard';
}
