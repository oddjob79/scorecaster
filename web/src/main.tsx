import "@fontsource-variable/bricolage-grotesque";
import "@fontsource-variable/manrope";
import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "@tanstack/react-router";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import { queryClient } from "./api/queryClient";
import { applyTheme, usePreferences } from "./preferences";
import { router } from "./router";

applyTheme(usePreferences.getState().theme);
usePreferences.subscribe((state, previous) => {
  if (state.theme !== previous.theme) applyTheme(state.theme);
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </StrictMode>,
);
