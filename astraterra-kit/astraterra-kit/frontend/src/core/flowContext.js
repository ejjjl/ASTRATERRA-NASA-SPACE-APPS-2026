// Shared by the guided flow and the features. Kept in its own file to avoid circular imports.
import { createContext, useContext } from "react";

export const FlowCtx = createContext({ screen: "welcome", go: () => {}, farmName: "" });
export const useFlow = () => useContext(FlowCtx);
