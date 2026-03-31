// app/api/result/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getResultImage, getResult } from '@/lib/store';

export const runtime = 'nodejs';

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const searchParams = req.nextUrl.searchParams;
  const typeParam = searchParams.get('type') || 'grid';
  const type = typeParam === 'cover' ? 'cover' : 'grid';

  try {
    const imageBuffer = getResultImage(id, type);

    if (!imageBuffer) {
      return NextResponse.json(
        { error: 'Result not found' },
        { status: 404 }
      );
    }

    return new NextResponse(new Uint8Array(imageBuffer), {
      headers: {
        'Content-Type': 'image/png',
        'Cache-Control': 'public, max-age=3600',
      },
    });
  } catch (error) {
    console.error('Get result error:', error);
    return NextResponse.json(
      { error: 'Failed to get result' },
      { status: 500 }
    );
  }
}
