// app/api/generate/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { generateMeme } from '@/lib/compose';
import { saveResult, getTodayCount } from '@/lib/store';

export const runtime = 'nodejs';
export const maxDuration = 60;

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get('file') as File | null;
    const theme = (formData.get('theme') as string) || 'workdog';

    if (!file) {
      return NextResponse.json(
        { error: 'No image file provided' },
        { status: 400 }
      );
    }

    // 验证文件类型
    if (!file.type.startsWith('image/')) {
      return NextResponse.json(
        { error: 'Invalid file type. Please upload an image.' },
        { status: 400 }
      );
    }

    // 验证文件大小 (10MB)
    if (file.size > 10 * 1024 * 1024) {
      return NextResponse.json(
        { error: 'File too large. Maximum size is 10MB.' },
        { status: 400 }
      );
    }

    // 转换为 Buffer
    const arrayBuffer = await file.arrayBuffer();
    const imageBuffer = Buffer.from(arrayBuffer);

    // 生成表情包
    const { id, gridBuffer, coverBuffer } = await generateMeme(imageBuffer, theme);

    // 保存结果
    saveResult(id, gridBuffer, coverBuffer, theme);

    // 获取今日计数
    const todayCount = getTodayCount();

    return NextResponse.json({
      id,
      todayCount,
    });
  } catch (error) {
    console.error('Generate error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Generation failed' },
      { status: 500 }
    );
  }
}
