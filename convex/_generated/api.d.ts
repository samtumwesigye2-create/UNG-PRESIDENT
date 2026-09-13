/* eslint-disable */
import type * as ResendOTP from "../ResendOTP.js";
import type * as auth from "../auth.js";
import type * as enrollment from "../enrollment.js";
import type * as executive from "../executive.js";
import type * as http from "../http.js";
import type * as macaly from "../macaly.js";
import type * as public_ from "../public.js";
import type * as staff from "../staff.js";
import type { ApiFromModules, FilterApi, FunctionReference } from "convex/server";

declare const fullApi: ApiFromModules<{
  ResendOTP: typeof ResendOTP;
  auth: typeof auth;
  enrollment: typeof enrollment;
  executive: typeof executive;
  http: typeof http;
  macaly: typeof macaly;
  public: typeof public_;
  staff: typeof staff;
}>;
export declare const api: FilterApi<typeof fullApi, FunctionReference<any, "public">>;
export declare const internal: FilterApi<typeof fullApi, FunctionReference<any, "internal">>;
export declare const components: {};
