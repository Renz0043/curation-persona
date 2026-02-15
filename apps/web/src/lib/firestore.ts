import {
  collection,
  doc,
  query,
  where,
  orderBy,
  limit,
  getDocs,
  getDoc,
  onSnapshot,
  Timestamp,
} from "firebase/firestore";
import { db } from "./firebase";
import type { Article, Collection, UserProfile, SourceConfig } from "./types";

// --- Timestamp 変換ヘルパー ---

function toDate(val: unknown): Date | undefined {
  if (val instanceof Timestamp) return val.toDate();
  if (val instanceof Date) return val;
  if (typeof val === "string" && val) return new Date(val);
  return undefined;
}

function convertArticleDoc(id: string, data: Record<string, unknown>): Article {
  return {
    ...data,
    id,
    published_at: toDate(data.published_at),
    relevance_score: (data.relevance_score as number) ?? 0,
    relevance_reason: (data.relevance_reason as string) ?? "",
    is_pickup: (data.is_pickup as boolean) ?? false,
    scoring_status: (data.scoring_status as Article["scoring_status"]) ?? "pending",
  } as Article;
}

function convertCollectionDoc(id: string, data: Record<string, unknown>): Collection {
  return {
    ...data,
    id,
    created_at: toDate(data.created_at) ?? new Date(),
  } as Collection;
}

// --- 読み取りヘルパー ---

/** 今日のコレクションを取得 */
export async function getTodayCollection(
  userId: string,
  dateStr?: string
): Promise<Collection | null> {
  const today = dateStr ?? new Date().toISOString().slice(0, 10);
  const q = query(
    collection(db, "collections"),
    where("user_id", "==", userId),
    where("date", "==", today),
    orderBy("created_at", "desc"),
    limit(1)
  );
  const snapshot = await getDocs(q);
  if (snapshot.empty) return null;
  const docSnap = snapshot.docs[0];
  return convertCollectionDoc(docSnap.id, docSnap.data());
}

/** コレクション内の記事一覧を取得 */
export async function getArticlesByCollection(
  collectionId: string,
  userId?: string
): Promise<Article[]> {
  const constraints = [where("collection_id", "==", collectionId)];
  if (userId) {
    constraints.push(where("user_id", "==", userId));
  }
  const q = query(collection(db, "articles"), ...constraints);
  const snapshot = await getDocs(q);
  return snapshot.docs.map((d) => convertArticleDoc(d.id, d.data()));
}

/** 記事詳細を取得 */
export async function getArticle(articleId: string): Promise<Article | null> {
  const docRef = doc(db, "articles", articleId);
  const snapshot = await getDoc(docRef);
  if (!snapshot.exists()) return null;
  return convertArticleDoc(snapshot.id, snapshot.data());
}

/** 過去コレクション一覧を取得（アーカイブ用） */
export async function getCollectionHistory(
  userId: string,
  maxResults = 30
): Promise<Collection[]> {
  const q = query(
    collection(db, "collections"),
    where("user_id", "==", userId),
    orderBy("created_at", "desc"),
    limit(maxResults)
  );
  const snapshot = await getDocs(q);
  return snapshot.docs.map((d) => convertCollectionDoc(d.id, d.data()));
}

/** ユーザープロファイルを取得 */
export async function getUserProfile(
  userId: string
): Promise<UserProfile | null> {
  const docRef = doc(db, "users", userId);
  const snapshot = await getDoc(docRef);
  if (!snapshot.exists()) return null;
  const data = snapshot.data();
  return {
    ...data,
    user_id: snapshot.id,
    interestProfileUpdatedAt: toDate(data.interestProfileUpdatedAt),
    createdAt: toDate(data.createdAt) ?? new Date(),
  } as UserProfile;
}

/** ブックマーク記事一覧を取得 */
export async function getBookmarkArticles(
  userId: string
): Promise<Article[]> {
  const bmCollectionId = `bm_${userId}`;
  return getArticlesByCollection(bmCollectionId, userId);
}

/** コレクションのリアルタイム監視 */
export function subscribeToCollection(
  collectionId: string,
  callback: (col: Collection | null) => void
): () => void {
  const docRef = doc(db, "collections", collectionId);
  return onSnapshot(docRef, (snapshot) => {
    if (!snapshot.exists()) {
      callback(null);
      return;
    }
    callback(convertCollectionDoc(snapshot.id, snapshot.data()));
  });
}

/** 記事のリアルタイム監視 */
export function subscribeToArticle(
  articleId: string,
  callback: (article: Article | null) => void
): () => void {
  const docRef = doc(db, "articles", articleId);
  return onSnapshot(docRef, (snapshot) => {
    if (!snapshot.exists()) {
      callback(null);
      return;
    }
    callback(convertArticleDoc(snapshot.id, snapshot.data()));
  });
}

// --- 書き込みヘルパー ---

/** ユーザーのソース設定を更新（API Route経由） */
export async function updateUserSources(
  userId: string,
  sources: SourceConfig[]
): Promise<void> {
  const res = await fetch("/api/users/sources", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ userId, sources }),
  });
  if (!res.ok) {
    throw new Error(`Failed to update sources: ${res.status}`);
  }
}
