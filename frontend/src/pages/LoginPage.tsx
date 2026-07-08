import { useState, type FormEvent } from "react";

interface LoginPageProps {
  onLogin: (username: string, password: string) => Promise<void>;
  onRegister: (username: string, fullName: string, password: string) => Promise<void>;
  onDemoLogin: () => Promise<void>;
}

type AuthMode = "login" | "register";

export function LoginPage({ onLogin, onRegister, onDemoLogin }: LoginPageProps) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      if (mode === "register") {
        await onRegister(username, fullName, password);
      } else {
        await onLogin(username, password);
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Authentication failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoLogin = async () => {
    setIsSubmitting(true);
    setError("");
    try {
      await onDemoLogin();
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Demo login failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-shell">
      <div className="login-card">
        <p className="eyebrow">Document Intelligence Platform</p>
        <h1>Reliable RAG Demo Console</h1>
        <p className="login-copy">
          Create your own demo account to test the full platform, or use the preloaded demo account for a quick guided walkthrough.
        </p>

        <div className="auth-toggle">
          <button
            type="button"
            className={mode === "login" ? "auth-toggle-button active" : "auth-toggle-button"}
            onClick={() => {
              setMode("login");
              setError("");
            }}
          >
            Login
          </button>
          <button
            type="button"
            className={mode === "register" ? "auth-toggle-button active" : "auth-toggle-button"}
            onClick={() => {
              setMode("register");
              setError("");
            }}
          >
            Register
          </button>
        </div>

        <form className="stack" onSubmit={handleSubmit}>
          {mode === "register" ? (
            <label className="field">
              <span>Full name</span>
              <input
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder="Example: Lakshit Tandon"
                minLength={1}
                maxLength={100}
                required
              />
            </label>
          ) : null}

          <label className="field">
            <span>Username</span>
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="letters, numbers, dot, hyphen, underscore"
              minLength={3}
              maxLength={40}
              pattern="[A-Za-z0-9_.-]+"
              required
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={mode === "register" ? 6 : 1}
              maxLength={128}
              required
            />
          </label>

          {error ? <p className="error-text">{error}</p> : null}

          <button className="primary-button" type="submit" disabled={isSubmitting}>
            {isSubmitting
              ? mode === "register"
                ? "Creating account..."
                : "Signing in..."
              : mode === "register"
                ? "Create Account"
                : "Enter Console"}
          </button>
          <button
            className="secondary-button"
            type="button"
            disabled={isSubmitting}
            onClick={handleDemoLogin}
          >
            Use Demo Account
          </button>
        </form>
      </div>
    </div>
  );
}
