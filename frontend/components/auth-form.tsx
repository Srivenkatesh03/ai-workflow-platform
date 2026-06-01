"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { ArrowRight, LockKeyhole, Mail, User } from "lucide-react";

import { useAuth } from "@/context/auth-context";

type AuthMode = "login" | "register";

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const { login, register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const isRegister = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      if (isRegister) {
        await register(name, email, password);
      } else {
        await login(email, password);
      }
      // router.push is handled by the AuthProvider redirect or within the auth functions
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Authentication failed");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-panel px-4 py-8 text-ink">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-6xl items-center">
        <section className="grid w-full overflow-hidden rounded border border-line bg-white lg:grid-cols-[1fr_420px]">
          <div className="hidden border-r border-line bg-ink p-10 text-white lg:block">
            <div className="flex h-full flex-col justify-between">
              <div>
                <div className="mb-10 flex h-11 w-11 items-center justify-center rounded bg-white text-ink">
                  <LockKeyhole size={22} aria-hidden="true" />
                </div>
                <h1 className="max-w-xl text-3xl font-semibold">Secure Workflow Operations</h1>
                <p className="mt-4 max-w-lg text-sm leading-6 text-slate-200">
                  Access workflow execution controls, AI automation logs, and operational alerts with role-aware
                  authentication.
                </p>
              </div>
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="rounded border border-white/20 p-3">
                  <p className="text-slate-300">Auth</p>
                  <p className="mt-1 font-semibold">JWT</p>
                </div>
                <div className="rounded border border-white/20 p-3">
                  <p className="text-slate-300">Roles</p>
                  <p className="mt-1 font-semibold">RBAC</p>
                </div>
                <div className="rounded border border-white/20 p-3">
                  <p className="text-slate-300">Sessions</p>
                  <p className="mt-1 font-semibold">Refresh</p>
                </div>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="p-6 sm:p-8">
            <div className="mb-7">
              <h2 className="text-2xl font-semibold">{isRegister ? "Create account" : "Sign in"}</h2>
              <p className="mt-2 text-sm text-slate-500">
                {isRegister ? "Register an operator account." : "Use your operator credentials."}
              </p>
            </div>

            <div className="space-y-4">
              {isRegister ? (
                <label className="block">
                  <span className="mb-2 block text-sm font-medium">Name</span>
                  <div className="flex h-11 items-center gap-2 rounded border border-line px-3">
                    <User size={16} className="text-slate-500" aria-hidden="true" />
                    <input
                      className="min-w-0 flex-1 outline-none"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      required
                      minLength={2}
                      autoComplete="name"
                    />
                  </div>
                </label>
              ) : null}

              <label className="block">
                <span className="mb-2 block text-sm font-medium">Email</span>
                <div className="flex h-11 items-center gap-2 rounded border border-line px-3">
                  <Mail size={16} className="text-slate-500" aria-hidden="true" />
                  <input
                    className="min-w-0 flex-1 outline-none"
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                    autoComplete="email"
                  />
                </div>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-medium">Password</span>
                <div className="flex h-11 items-center gap-2 rounded border border-line px-3">
                  <LockKeyhole size={16} className="text-slate-500" aria-hidden="true" />
                  <input
                    className="min-w-0 flex-1 outline-none"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                    minLength={8}
                    autoComplete={isRegister ? "new-password" : "current-password"}
                  />
                </div>
              </label>
            </div>

            {error ? <p className="mt-4 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}

            <button
              className="mt-6 flex h-11 w-full items-center justify-center gap-2 rounded bg-ink px-4 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Submitting" : isRegister ? "Create account" : "Sign in"}
              <ArrowRight size={16} aria-hidden="true" />
            </button>

            <p className="mt-5 text-center text-sm text-slate-500">
              {isRegister ? "Already have an account?" : "Need an account?"}{" "}
              <Link className="font-medium text-ink underline" href={isRegister ? "/login" : "/register"}>
                {isRegister ? "Sign in" : "Register"}
              </Link>
            </p>
          </form>
        </section>
      </div>
    </div>
  );
}

