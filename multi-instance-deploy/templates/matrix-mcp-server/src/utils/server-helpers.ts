import { createMatrixClient } from "../matrix/client.js";
import { TokenExchangeConfig } from "../auth/tokenExchange.js";

// Environment configuration
export const ENABLE_OAUTH = process.env.ENABLE_OAUTH === "true";
export const ENABLE_TOKEN_EXCHANGE = process.env.ENABLE_TOKEN_EXCHANGE === "true";
export const defaultDeviceId = process.env.MATRIX_DEVICE_ID || "";
export const defaultAccessToken = process.env.MATRIX_ACCESS_TOKEN || "";
export const defaultUserId = process.env.MATRIX_USER_ID || "";
export const defaultHomeserverUrl =
  process.env.MATRIX_HOMESERVER_URL || "https://localhost:8008/";

// OAuth/Token exchange configuration
export const tokenExchangeConfig: TokenExchangeConfig = {
  idpUrl: process.env.IDP_ISSUER_URL || "",
  clientId: process.env.MATRIX_CLIENT_ID || "",
  clientSecret: process.env.MATRIX_CLIENT_SECRET || "",
  matrixClientId: process.env.MATRIX_CLIENT_ID || "",
};

/**
 * Helper function to get access token based on OAuth mode.
 * Enhanced v2: .env token is authoritative. Header tokens are accepted
 * but validated against .env; mismatches trigger a warning and fallback.
 */
export function getAccessToken(
  headers: Record<string, string | string[] | undefined> | undefined,
  oauthToken: string | undefined
): string {
  const matrixTokenFromHeader = headers?.["matrix_access_token"];
  let headerToken: string | undefined;

  // Extract header token if present
  if (matrixTokenFromHeader) {
    if (Array.isArray(matrixTokenFromHeader)) {
      headerToken = matrixTokenFromHeader.find(
        (token) => typeof token === "string" && token !== ""
      );
    } else if (
      typeof matrixTokenFromHeader === "string" &&
      matrixTokenFromHeader !== ""
    ) {
      headerToken = matrixTokenFromHeader;
    }
  }

  // If header token exists, validate it against .env token
  if (headerToken) {
    if (defaultAccessToken && headerToken !== defaultAccessToken) {
      console.warn(
        `[TOKEN-GUARD] Header token (${headerToken.substring(0, 8)}...) ` +
        `differs from .env token (${defaultAccessToken.substring(0, 8)}...). ` +
        `Falling back to authoritative .env token.`
      );
      return defaultAccessToken;
    }
    // Header token matches .env — use it
    return headerToken;
  }

  // If no valid matrix_access_token, and OAuth is enabled, use oauthToken
  if (ENABLE_OAUTH && typeof oauthToken === "string" && oauthToken !== "") {
    return oauthToken;
  }

  // Fall back to environment variable (authoritative source)
  return defaultAccessToken;
}

/**
 * Helper function to extract matrixUserId and homeserverUrl from headers
 */
export function getMatrixContext(
  headers: Record<string, string | string[] | undefined> | undefined
): { matrixUserId: string; homeserverUrl: string } {
  const matrixUserId =
    (Array.isArray(headers?.["matrix_user_id"])
      ? headers?.["matrix_user_id"][0]
      : headers?.["matrix_user_id"]) || defaultUserId;
  const homeserverUrl =
    (Array.isArray(headers?.["matrix_homeserver_url"])
      ? headers?.["matrix_homeserver_url"][0]
      : headers?.["matrix_homeserver_url"]) || defaultHomeserverUrl;
  return { matrixUserId, homeserverUrl };
}

/**
 * Helper function to create Matrix client with proper configuration
 */
export async function createConfiguredMatrixClient(
  homeserverUrl: string,
  matrixUserId: string,
  accessToken: string
) {
  return createMatrixClient({
    homeserverUrl,
    userId: matrixUserId,
    accessToken,
    deviceId: defaultDeviceId,
    enableOAuth: ENABLE_OAUTH,
    tokenExchangeConfig: tokenExchangeConfig,
    enableTokenExchange: ENABLE_TOKEN_EXCHANGE,
  });
}
