'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

interface MemeMeta {
  id: string;
  theme: string;
  createdAt: number;
  todayCount: number;
}

export default function ResultPage() {
  const params = useParams();
  const id = params.id as string;
  
  const [meta, setMeta] = useState<MemeMeta | null>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(false);

  useEffect(() => {
    fetch(`/api/meta/${id}`)
      .then(res => res.json())
      .then(data => {
        if (!data.error) {
          setMeta(data);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const handleCopyLink = async () => {
    const url = `${window.location.origin}/r/${id}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      alert('复制失败，请手动复制链接');
    }
  };

  const handleDownload = async (type: 'grid' | 'cover') => {
    setDownloadProgress(true);
    try {
      const response = await fetch(`/api/result/${id}?type=${type}`);
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = type === 'grid' ? 'meme-grid.png' : 'meme-cover.png';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      alert('下载失败');
    }
    setDownloadProgress(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 to-amber-50">
        <div className="text-center">
          <div className="text-4xl mb-4">🐕</div>
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-amber-50">
      <div className="max-w-md mx-auto px-4 py-8">
        {/* 标题 */}
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-800">
            🎉 生成完成！
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            今日第 {meta?.todayCount || '?'} 只打工狗
          </p>
        </div>

        {/* 九宫格预览 */}
        <div className="bg-white rounded-2xl shadow-lg p-4 mb-6">
          <img
            src={`/api/result/${id}?type=grid&t=${Date.now()}`}
            alt="九宫格表情包"
            className="w-full rounded-lg"
            onError={(e) => {
              (e.target as HTMLImageElement).src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="50%" x="50%" text-anchor="middle" font-size="20">加载失败</text></svg>';
            }}
          />
        </div>

        {/* 下载按钮 */}
        <div className="space-y-3 mb-6">
          <button
            onClick={() => handleDownload('grid')}
            disabled={downloadProgress}
            className="w-full py-4 bg-orange-500 text-white rounded-xl font-bold hover:bg-orange-600 transition-all shadow-lg hover:shadow-xl disabled:opacity-50"
          >
            📥 下载九宫格
          </button>
          <button
            onClick={() => handleDownload('cover')}
            disabled={downloadProgress}
            className="w-full py-4 bg-amber-500 text-white rounded-xl font-bold hover:bg-amber-600 transition-all shadow-lg hover:shadow-xl disabled:opacity-50"
          >
            📱 下载竖版封面（小红书/朋友圈）
          </button>
        </div>

        {/* 分享 */}
        <div className="bg-white rounded-2xl shadow-lg p-4 mb-6">
          <p className="text-gray-600 text-sm mb-3 text-center">
            分享给朋友看看 🐕
          </p>
          <button
            onClick={handleCopyLink}
            className="w-full py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-all"
          >
            {copied ? '✅ 已复制！' : '🔗 复制分享链接'}
          </button>
        </div>

        {/* 付费解锁提示 */}
        <div className="bg-gradient-to-r from-orange-400 to-amber-400 rounded-2xl p-4 text-center text-white">
          <p className="font-bold mb-1">高清无水印版本</p>
          <p className="text-sm opacity-90 mb-3">
            ¥9.9 解锁，永久可用的表情包
          </p>
          <button className="bg-white text-orange-500 px-8 py-2 rounded-full font-bold hover:bg-opacity-90 transition-all">
            立即解锁
          </button>
        </div>

        {/* 返回首页 */}
        <div className="mt-6 text-center">
          <a href="/" className="text-orange-500 hover:underline">
            ← 再做一组
          </a>
        </div>
      </div>
    </div>
  );
}
