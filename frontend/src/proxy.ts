import { NextRequest, NextResponse } from "next/server";

// 앱을 나 혼자만 쓸 수 있게, 브라우저 기본 로그인창(Basic Auth)으로 막는다.
// BASIC_AUTH_USER/BASIC_AUTH_PASSWORD가 설정 안 돼 있으면(로컬 개발 등) 그냥 통과시킨다.
export function proxy(request: NextRequest) {
  const user = process.env.BASIC_AUTH_USER;
  const password = process.env.BASIC_AUTH_PASSWORD;

  if (!user || !password) {
    return NextResponse.next();
  }

  const authHeader = request.headers.get("authorization");
  if (authHeader?.startsWith("Basic ")) {
    const decoded = atob(authHeader.slice("Basic ".length));
    const separatorIndex = decoded.indexOf(":");
    const reqUser = decoded.slice(0, separatorIndex);
    const reqPassword = decoded.slice(separatorIndex + 1);
    if (reqUser === user && reqPassword === password) {
      return NextResponse.next();
    }
  }

  return new NextResponse("인증이 필요합니다.", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Steady Listening"' },
  });
}

export const config = {
  matcher: "/((?!_next/static|_next/image|favicon.ico).*)",
};
