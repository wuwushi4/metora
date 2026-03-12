/**
 * Dashboard 儀表板類型定義
 */

/**
 * 時間範圍枚舉
 */
export type TimeRange = 'today' | 'this_week' | 'this_month' | 'last_7_days' | 'last_30_days' | 'all'

/**
 * 聊天統計
 */
export interface ChatStats {
  total_sessions: number
  total_messages: number
  daily_avg_messages: number
  graph_type_distribution: Record<string, number>
}

/**
 * 問題標籤計數
 */
export interface IssueTagCount {
  tag: string
  count: number
}

/**
 * 反饋統計
 */
export interface FeedbackStats {
  total_feedbacks: number
  thumbs_up_count: number
  thumbs_down_count: number
  thumbs_up_rate: number
  feedback_rate: number
  pending_review_count: number
  top_issue_tags: IssueTagCount[]
}

/**
 * Admin 儀表板統計數據
 */
export interface AdminDashboardStats {
  time_range: string
  period_start: string | null
  period_end: string
  chat_stats: ChatStats
  feedback_stats: FeedbackStats
}

/**
 * 基本統計
 */
export interface BasicStats {
  total_sessions: number
  total_messages: number
}

/**
 * User 儀表板資訊
 */
export interface UserDashboardInfo {
  username: string
  welcome_message: string
  basic_stats: BasicStats
}
