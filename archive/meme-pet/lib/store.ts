// lib/store.ts
import fs from 'fs';
import path from 'path';

const STORE_DIR = '/tmp/meme-pet-results';

// 确保存储目录存在
if (!fs.existsSync(STORE_DIR)) {
  fs.mkdirSync(STORE_DIR, { recursive: true });
}

export interface MemeResult {
  id: string;
  theme: string;
  createdAt: number;
  gridPath: string;
  coverPath: string;
}

export function saveResult(id: string, gridBuffer: Buffer, coverBuffer: Buffer, theme: string): MemeResult {
  const gridPath = path.join(STORE_DIR, `${id}-grid.png`);
  const coverPath = path.join(STORE_DIR, `${id}-cover.png`);
  
  fs.writeFileSync(gridPath, gridBuffer);
  fs.writeFileSync(coverPath, coverBuffer);
  
  const result: MemeResult = {
    id,
    theme,
    createdAt: Date.now(),
    gridPath,
    coverPath,
  };
  
  // 保存元数据
  const metaPath = path.join(STORE_DIR, `${id}.json`);
  fs.writeFileSync(metaPath, JSON.stringify(result));
  
  return result;
}

export function getResult(id: string): MemeResult | null {
  const metaPath = path.join(STORE_DIR, `${id}.json`);
  
  if (!fs.existsSync(metaPath)) {
    return null;
  }
  
  const content = fs.readFileSync(metaPath, 'utf-8');
  return JSON.parse(content);
}

export function getResultImage(id: string, type: 'grid' | 'cover'): Buffer | null {
  const result = getResult(id);
  
  if (!result) {
    return null;
  }
  
  const filePath = type === 'grid' ? result.gridPath : result.coverPath;
  
  if (!fs.existsSync(filePath)) {
    return null;
  }
  
  return fs.readFileSync(filePath);
}

// 获取今日生成数量
export function getTodayCount(): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayStart = today.getTime();
  
  let count = 0;
  
  const files = fs.readdirSync(STORE_DIR);
  for (const file of files) {
    if (file.endsWith('.json')) {
      const metaPath = path.join(STORE_DIR, file);
      const content = fs.readFileSync(metaPath, 'utf-8');
      const result = JSON.parse(content);
      
      if (result.createdAt >= todayStart) {
        count++;
      }
    }
  }
  
  return count;
}
