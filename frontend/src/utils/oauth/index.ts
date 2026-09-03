import AuthAPI, { type OAuthProvider } from "@/api/module_system/auth";

/**
 * 跳转浏览器至后端 OAuth 入口，授权完成后回到 `redirect_uri`（通常为当前站点 /login）。
 */
export function startOAuthLogin(provider: OAuthProvider, redirect?: string): void {
  const redirectUri = new URL("/login", window.location.origin);
  if (redirect && redirect !== "/login") {
    redirectUri.searchParams.set("redirect", redirect);
  }
  window.location.href = AuthAPI.getOAuthLoginUrl(provider, redirectUri.toString());
}
