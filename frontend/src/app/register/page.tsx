import { AuthLayout } from "@/features/auth/components/AuthLayout";
import { RegisterForm } from "@/features/auth/components/RegisterForm";

export default function RegisterPage() {
  return (
    <AuthLayout
      title="Create an account"
      description="Enter your details to get started with ProcureAI"
    >
      <RegisterForm />
    </AuthLayout>
  );
}
