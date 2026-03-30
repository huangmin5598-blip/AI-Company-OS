// lib/compose.ts
import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { removeBackgroundBuffer } from './removebg';

interface LayoutConfig {
  name: string;
  nameCn: string;
  width: number;
  height: number;
  overlays: Array<{
    x: number;
    y: number;
    width: number;
    height: number;
  }>;
}

export async function loadLayout(theme: string): Promise<LayoutConfig> {
  const layoutPath = path.join(process.cwd(), 'lib/templates', theme, 'layout.json');
  const content = fs.readFileSync(layoutPath, 'utf-8');
  return JSON.parse(content);
}

export async function generateMeme(
  imageBuffer: Buffer,
  theme: string = 'workdog'
): Promise<{ id: string; gridBuffer: Buffer; coverBuffer: Buffer }> {
  // 1. 抠图
  const cutoutBuffer = await removeBackgroundBuffer(imageBuffer);

  // 2. 加载布局配置
  const layout = await loadLayout(theme);
  const templateDir = path.join(process.cwd(), 'lib/templates', theme);

  // 3. 生成 9 张合成图
  const composites: sharp.OverlayOptions[] = [];

  for (let i = 1; i <= 9; i++) {
    const templatePath = path.join(templateDir, `${i}.png`);
    
    // 读取模板
    const templateBuffer = fs.readFileSync(templatePath);
    
    // 调整抠图大小并合成到模板
    const resizedCutout = await sharp(cutoutBuffer)
      .resize(layout.overlays[0].width, layout.overlays[0].height, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
      .toBuffer();

    const composite = await sharp(templateBuffer)
      .composite([{
        input: resizedCutout,
        left: layout.overlays[0].x,
        top: layout.overlays[0].y,
      }])
      .png()
      .toBuffer();

    composites.push({
      input: composite,
    });
  }

  // 4. 拼成九宫格
  const gridWidth = layout.width * 3;
  const gridHeight = layout.height * 3;

  const gridBuffer = await sharp({
    create: {
      width: gridWidth,
      height: gridHeight,
      channels: 4,
      background: { r: 255, g: 255, b: 255, alpha: 1 },
    },
  })
    .composite(composites.flatMap((comp, idx) => {
      const col = idx % 3;
      const row = Math.floor(idx / 3);
      return [{
        input: comp.input,
        left: col * layout.width,
        top: row * layout.height,
      }];
    }))
    .png()
    .toBuffer();

  // 5. 生成竖版封面 (用于小红书/朋友圈)
  const coverBuffer = await sharp(gridBuffer)
    .resize(540, 960, { fit: 'cover' })
    .png()
    .toBuffer();

  // 6. 生成唯一 ID
  const id = generateId();

  return { id, gridBuffer, coverBuffer };
}

function generateId(): string {
  const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  for (let i = 0; i < 8; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}
