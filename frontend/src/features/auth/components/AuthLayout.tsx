export function AuthLayout({
  children,
  title,
  description,
}: {
  children: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="flex min-h-screen bg-background">
      {/* Left Branding Panel (Hidden on Mobile) */}
      <div className="hidden lg:flex w-1/2 flex-col justify-between bg-primary p-12 text-primary-foreground">
        <div>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded bg-primary-foreground text-primary font-bold text-xl">
              P
            </div>
            <span className="text-2xl font-bold tracking-tight">ProcureAI</span>
          </div>
          <div className="mt-24 max-w-md">
            <h1 className="text-4xl font-bold leading-tight tracking-tight">
              Enterprise Procurement Intelligence
            </h1>
            <p className="mt-6 text-lg text-primary-foreground/80">
              Streamline your vendor evaluation, compliance checks, and pricing analysis with AI-driven insights. Built for modern enterprises.
            </p>
          </div>
        </div>
        <div className="text-sm text-primary-foreground/60">
          © {new Date().getFullYear()} ProcureAI. All rights reserved.
        </div>
      </div>

      {/* Right Auth Panel */}
      <div className="flex w-full lg:w-1/2 items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center lg:text-left">
            <h2 className="text-3xl font-bold tracking-tight">{title}</h2>
            <p className="text-muted-foreground mt-2">{description}</p>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}
