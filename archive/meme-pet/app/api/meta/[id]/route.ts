// app/api/meta/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getResult, getTodayCount } from '@/lib/store';

export const runtime = 'nodejs';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const result = getResult(id);

    if (!result) {
      return NextResponse.json(
        { error: 'Result not found' },
        { status: 404 }
      );
    }

    const todayCount = getTodayCount();

    return NextResponse.json({
      id: result.id,
      theme: result.theme,
      createdAt: result.createdAt,
      todayCount,
    });
  } catch (error) {
    console.error('Get meta error:', error);
    return NextResponse.json(
      { error: 'Failed to get meta' },
      { status: 500 }
    );
  }
}
