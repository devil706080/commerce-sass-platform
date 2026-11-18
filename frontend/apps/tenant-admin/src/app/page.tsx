"use client";

import { useState } from "react";
import { AdminLogin, AuthState } from "@/features/auth/AdminLogin";
import { CatalogueWorkspace } from "@/features/catalogue/CatalogueWorkspace";

export default function Page() {
  const [state, setState] = useState<AuthState>("checking");
  return state === "authorized" ? <CatalogueWorkspace /> : <AdminLogin onState={setState} />;
}
