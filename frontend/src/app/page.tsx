"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { getTokens } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  useEffect(() => {
    router.replace(getTokens() ? "/dashboard" : "/login");
  }, [router]);
  return null;
}
