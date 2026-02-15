// Firestore データモデルに対応する TypeScript 型定義
// バックエンド: services/agents/shared/models.py に準拠

export type CollectionStatus =
  | "collecting"
  | "scoring"
  | "researching"
  | "completed"
  | "failed";

export type ScoringStatus = "pending" | "scoring" | "scored";

export type ResearchStatus = "pending" | "researching" | "completed" | "failed";

export type SourceType = "rss" | "website" | "newsletter" | "api" | "bookmark";

// --- Firestore documents ---

/** collections/{collectionId} */
export type Collection = {
  id: string;
  user_id: string;
  date: string; // "2025-01-15" (ブックマークは "")
  status: CollectionStatus;
  created_at: Date;
};

/** articles/{articleId}  articleId = "{collectionId}_{urlHash8桁}" */
export type Article = {
  id: string;
  collection_id: string;
  user_id: string;
  title: string;
  url: string;
  source: string;
  source_type: SourceType;
  content?: string;
  meta_description?: string;
  og_image?: string;
  published_at?: Date;

  // スコアリング
  scoring_status: ScoringStatus;
  relevance_score: number;
  relevance_reason: string;
  is_pickup: boolean;

  // 深掘りレポート
  research_status?: ResearchStatus;
  deep_dive_report?: string; // Markdown
  cross_industry_feedback?: CrossIndustryFeedback;

  // ユーザーフィードバック
  user_rating?: number; // 1-5
  user_comment?: string;
};

export type CrossIndustryPerspective = {
  industry: string;
  expert_comment: string;
};

export type CrossIndustryFeedback = {
  abstracted_challenge: string;
  perspectives: CrossIndustryPerspective[];
};

/** users/{userId} */
export type SourceConfig = {
  id: string;
  type: SourceType;
  name: string;
  enabled: boolean;
  config?: Record<string, unknown>;
};

export type UserProfile = {
  user_id: string;
  sources: SourceConfig[];
  api_key?: string;
  interestProfile?: string;
  interestProfileUpdatedAt?: Date;
  createdAt: Date;
};
