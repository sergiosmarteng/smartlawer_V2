import { NextResponse } from 'next/server';
import { getCurrentUser, getAuthUserId } from '@/lib/auth';

export async function GET() {
  const userId = await getAuthUserId();

  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const user = await getCurrentUser();

  return NextResponse.json({ user });
}
