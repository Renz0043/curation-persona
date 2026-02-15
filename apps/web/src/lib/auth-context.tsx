"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import {
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut as firebaseSignOut,
  type User,
} from "firebase/auth";
import { auth } from "./firebase";

type AuthState = {
  user: User | null;
  loading: boolean;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthState>({
  user: null,
  loading: true,
  signOut: async () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

const TEST_EMAIL = "test@example.com";
const TEST_PASSWORD = "testpassword123";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        setUser(firebaseUser);
        setLoading(false);
        return;
      }

      // Emulator環境ではテストユーザーで自動サインイン
      if (process.env.NEXT_PUBLIC_USE_EMULATOR === "true") {
        try {
          const cred = await signInWithEmailAndPassword(
            auth,
            TEST_EMAIL,
            TEST_PASSWORD
          );
          setUser(cred.user);
        } catch {
          // ユーザーが存在しない場合は作成
          try {
            const cred = await createUserWithEmailAndPassword(
              auth,
              TEST_EMAIL,
              TEST_PASSWORD
            );
            setUser(cred.user);
          } catch (e) {
            console.error("Auto sign-in failed:", e);
            setUser(null);
          }
        }
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const handleSignOut = async () => {
    await firebaseSignOut(auth);
  };

  if (loading) {
    return (
      <div
        className="flex items-center justify-center min-h-screen"
        style={{ color: "var(--color-text-muted)" }}
      >
        <div className="flex flex-col items-center gap-3">
          <div
            className="w-8 h-8 rounded-full border-2 border-t-transparent animate-spin"
            style={{ borderColor: "var(--color-primary)", borderTopColor: "transparent" }}
          />
          <span className="text-sm">読み込み中...</span>
        </div>
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, loading, signOut: handleSignOut }}>
      {children}
    </AuthContext.Provider>
  );
}
