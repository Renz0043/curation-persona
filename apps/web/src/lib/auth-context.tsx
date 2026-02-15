"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

const FIXED_USER_ID =
  process.env.NEXT_PUBLIC_FIXED_USER_ID || "default_user";
const USE_EMULATOR = process.env.NEXT_PUBLIC_USE_EMULATOR === "true";

type FixedUser = { uid: string };

type AuthState = {
  user: FixedUser | null;
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
  const [user, setUser] = useState<FixedUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (USE_EMULATOR) {
      // Emulator環境: Firebase Auth で自動サインイン
      (async () => {
        try {
          const { auth } = await import("./firebase");
          const {
            onAuthStateChanged,
            signInWithEmailAndPassword,
            createUserWithEmailAndPassword,
          } = await import("firebase/auth");

          onAuthStateChanged(auth, async (firebaseUser) => {
            if (firebaseUser) {
              setUser({ uid: firebaseUser.uid });
              setLoading(false);
              return;
            }
            try {
              const cred = await signInWithEmailAndPassword(
                auth,
                TEST_EMAIL,
                TEST_PASSWORD
              );
              setUser({ uid: cred.user.uid });
            } catch {
              try {
                const cred = await createUserWithEmailAndPassword(
                  auth,
                  TEST_EMAIL,
                  TEST_PASSWORD
                );
                setUser({ uid: cred.user.uid });
              } catch (e) {
                console.error("Auto sign-in failed:", e);
                setUser(null);
              }
            }
            setLoading(false);
          });
        } catch (e) {
          console.error("Firebase auth init failed:", e);
          setUser({ uid: FIXED_USER_ID });
          setLoading(false);
        }
      })();
    } else {
      // 本番環境: 固定user_idを即座に返す
      setUser({ uid: FIXED_USER_ID });
      setLoading(false);
    }
  }, []);

  const handleSignOut = async () => {
    // no-op: 認証なしモードではサインアウト不要
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
