// lib/removebg.ts
import fs from 'fs';

export async function removeBackgroundBuffer(imageBuffer: Buffer): Promise<Buffer> {
  const apiKey = process.env.REMOVEBG_API_KEY;
  
  if (!apiKey) {
    throw new Error('REMOVEBG_API_KEY not configured');
  }

  // 转换 Buffer 到 Uint8Array
  const uint8Array = new Uint8Array(imageBuffer);
  
  // 使用 native fetch + FormData (Node.js 22+ 支持)
  const form = new FormData();
  form.append('image_file', new Blob([uint8Array]), 'input.png');
  form.append('size', 'auto');
  form.append('format', 'png');

  const response = await fetch('https://api.remove.bg/v1.0/removebg', {
    method: 'POST',
    headers: {
      'X-Api-Key': apiKey,
    },
    body: form as any,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`remove.bg API error: ${error}`);
  }

  return Buffer.from(await response.arrayBuffer());
}

export async function removeBackground(imagePath: string): Promise<Buffer> {
  const imageBuffer = fs.readFileSync(imagePath);
  return removeBackgroundBuffer(imageBuffer);
}
