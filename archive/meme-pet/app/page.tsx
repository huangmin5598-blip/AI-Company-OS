'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.type.startsWith('image/')) {
        setError('请上传图片文件');
        return;
      }
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('图片大小不能超过10MB');
        return;
      }
      setFile(selectedFile);
      setError(null);
      
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target?.result as string);
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleSubmit = async () => {
    if (!file) return;
    
    setUploading(true);
    setProgress(10);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('theme', 'workdog');

    try {
      const progressInterval = setInterval(() => {
        setProgress(p => Math.min(p + 10, 80));
      }, 500);

      const response = await fetch('/api/generate', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || '生成失败');
      }

      const data = await response.json();
      setProgress(100);
      
      setTimeout(() => {
        router.push(`/r/${data.id}`);
      }, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : '生成失败，请重试');
      setUploading(false);
      setProgress(0);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type.startsWith('image/')) {
      if (fileInputRef.current) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(droppedFile);
        fileInputRef.current.files = dataTransfer.files;
        handleFileChange({ target: { files: dataTransfer.files } } as any);
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#F8F6F1' }}>
      {/* 第一屏 */}
      <div className="max-w-[960px] mx-auto px-6 pt-16 pb-12">
        {/* Logo / 产品名称 */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-between gap-4 mb-6 w-full max-w-md mx-auto">
            <div className="flex items-center gap-2">
              <span className="text-3xl">🐕</span>
              <span className="text-xl font-semibold" style={{ color: '#1F1F1F' }}>打工狗表情包</span>
            </div>
            <a
              href="/about"
              className="px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 hover:shadow-md"
              style={{ 
                backgroundColor: '#FFFFFF', 
                color: '#6B6B6B',
                border: '1px solid #E8E3D9'
              }}
            >
              关于我们
            </a>
          </div>
          
          {/* 主标题 */}
          <h1 className="text-4xl md:text-5xl font-bold mb-4" style={{ color: '#0066FF', lineHeight: 1.2 }}>
            把你家狗，变成真正的打工人
          </h1>
          
          {/* 副标题 */}
          <p className="text-lg md:text-xl" style={{ color: '#6B6B6B' }}>
            上传一张照片，自动生成能直接发聊天的九宫格表情包。
          </p>
        </div>

        {/* 上传卡片 */}
        <div 
          className="rounded-3xl p-8 mb-6 transition-all duration-300 cursor-pointer relative overflow-hidden"
          style={{ 
            backgroundColor: '#FFFFFF', 
            boxShadow: isDragging ? '0 8px 30px rgba(201, 139, 95, 0.3)' : '0 4px 20px rgba(0, 0, 0, 0.08)',
            border: isDragging ? '2px solid #C98B5F' : '1px solid #E8E3D9'
          }}
          onClick={() => !preview && fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          {/* 拖拽时的覆盖层 */}
          {isDragging && (
            <div 
              className="absolute inset-0 flex items-center justify-center z-10"
              style={{ backgroundColor: 'rgba(255, 247, 237, 0.95)' }}
            >
              <div className="text-center">
                <svg className="w-16 h-16 mx-auto mb-3 animate-bounce" style={{ color: '#C98B5F' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-lg font-semibold" style={{ color: '#C98B5F' }}>松开鼠标上传图片</p>
              </div>
            </div>
          )}
          {preview ? (
            <div className="text-center">
              <div className="relative inline-block group">
                <img 
                  src={preview} 
                  alt="预览" 
                  className="max-h-72 rounded-2xl shadow-md"
                />
                <button
                  onClick={(e) => { e.stopPropagation(); setFile(null); setPreview(null); }}
                  className="absolute -top-3 -right-3 w-8 h-8 rounded-full flex items-center justify-center text-white text-xl shadow-md transition-all duration-200 hover:scale-110 hover:shadow-lg"
                  style={{ backgroundColor: '#1F1F1F' }}
                >
                  ×
                </button>
              </div>
              <p className="mt-4 text-sm" style={{ color: '#6B6B6B' }}>点击图片可重新选择</p>
            </div>
          ) : (
            <div className="py-12">
              {/* 上传图标 - 更醒目 */}
              <div className="flex justify-center mb-6">
                <div 
                  className="w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 hover:scale-110"
                  style={{ 
                    backgroundColor: '#FFF7ED',
                    border: '3px dashed #C98B5F'
                  }}
                >
                  <svg className="w-12 h-12" style={{ color: '#C98B5F' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
              
              {/* 主文案 */}
              <p className="text-xl font-semibold mb-2" style={{ color: '#1F1F1F' }}>
                点击或拖拽上传宠物照片
              </p>
              
              {/* 辅助文案 */}
              <p className="text-sm" style={{ color: '#6B6B6B' }}>
                支持 JPG / PNG，建议使用正脸清晰照片
              </p>
            </div>
          )}
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>

        {/* 主按钮 - 更醒目 */}
        <div className="mb-4">
          {uploading ? (
            <div className="text-center py-4">
              {/* Loading 动画 */}
              <div className="relative w-20 h-20 mx-auto mb-4">
                {/* 外圈旋转 */}
                <div className="absolute inset-0 rounded-full border-4 border-t-transparent animate-spin" style={{ borderColor: '#C98B5F', borderTopColor: 'transparent' }}></div>
                {/* 内圈反向旋转 */}
                <div className="absolute inset-2 rounded-full border-4 border-b-transparent animate-spin" style={{ borderColor: '#E8E3D9', borderBottomColor: 'transparent', animationDirection: 'reverse', animationDuration: '1.2s' }}></div>
                {/* 中心图标 */}
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl">🐕</span>
                </div>
              </div>
              
              {/* 进度条 */}
              <div className="w-full rounded-full h-3 mb-3 overflow-hidden" style={{ backgroundColor: '#E8E3D9' }}>
                <div 
                  className="h-full rounded-full transition-all duration-300"
                  style={{ width: `${progress}%`, backgroundColor: '#222222' }}
                />
              </div>
              <p style={{ color: '#6B6B6B' }} className="flex items-center justify-center gap-2">
                {progress < 100 ? (
                  <>
                    <span className="inline-block w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: '#C98B5F' }}></span>
                    生成中...
                  </>
                ) : (
                  <>
                    <span className="text-green-500">✓</span>
                    准备跳转...
                  </>
                )}
              </p>
            </div>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={!file}
              className="w-full py-5 rounded-2xl text-lg font-semibold transition-all duration-300 group relative overflow-hidden"
              style={{ 
                backgroundColor: file ? '#C98B5F' : '#E8E3D9',
                color: file ? '#FFFFFF' : '#6B6B6B',
                cursor: file ? 'pointer' : 'not-allowed',
                boxShadow: file ? '0 4px 14px rgba(201, 139, 95, 0.4)' : 'none'
              }}
            >
              {/* 悬停时的光效 */}
              {file && (
                <span 
                  className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                  style={{ 
                    background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent)',
                    transform: 'translateX(-100%)'
                  }}
                />
              )}
              <span className="relative flex items-center justify-center gap-2">
                {file ? (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    开始生成表情包
                  </>
                ) : (
                  '请先上传照片'
                )}
              </span>
            </button>
          )}
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mt-4 p-4 rounded-xl text-center" style={{ backgroundColor: '#FEF2F2', color: '#DC2626' }}>
            {error}
          </div>
        )}

        {/* 轻信任文案 */}
        <p className="text-center text-sm mt-6" style={{ color: '#6B6B6B' }}>
          免费预览，高清版可下载
        </p>

        {/* 社交分享按钮 */}
        <div className="mt-6 text-center">
          <button
            onClick={() => {
              if (navigator.share) {
                navigator.share({
                  title: '打工狗表情包',
                  text: '快来生成你家的打工狗表情包！',
                  url: window.location.href,
                }).catch(() => {
                  // 用户取消分享或分享失败，静默处理
                });
              } else {
                // 不支持 Web Share API，复制链接
                navigator.clipboard.writeText(window.location.href).then(() => {
                  alert('链接已复制，快去分享给朋友吧！');
                }).catch(() => {
                  alert('复制失败，请手动复制链接分享');
                });
              }
            }}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-full text-base font-medium transition-all duration-300 hover:shadow-md hover:-translate-y-0.5"
            style={{ 
              backgroundColor: '#FFFFFF', 
              color: '#0066FF',
              border: '1px solid #0066FF'
            }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
            分享给朋友
          </button>
        </div>
      </div>

      {/* 第二屏：结果预览区 */}
      <div className="max-w-[960px] mx-auto px-6 py-12">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold mb-2" style={{ color: '#1F1F1F' }}>
            生成后大概长这样
          </h2>
        </div>
        
        {/* 示例九宫格 */}
        <div className="bg-white rounded-3xl p-6 shadow-sm" style={{ border: '1px solid #E8E3D9' }}>
          <div className="grid grid-cols-3 gap-2 max-w-md mx-auto">
            {[
              { emoji: '💼', text: '早会打卡' },
              { emoji: '📋', text: '收到' },
              { emoji: '🔥', text: 'KPI 达成' },
              { emoji: '💪', text: '加班中' },
              { emoji: '☕', text: '摸鱼时间' },
              { emoji: '📈', text: '季度汇报' },
              { emoji: '🎉', text: '发工资' },
              { emoji: '😤', text: '背锅' },
              { emoji: '🏖️', text: '带薪休假' },
            ].map((item, index) => (
              <div 
                key={index}
                className="aspect-square rounded-2xl flex flex-col items-center justify-center text-center p-2"
                style={{ backgroundColor: '#F8F6F1' }}
              >
                <span className="text-2xl mb-1">{item.emoji}</span>
                <span className="text-xs" style={{ color: '#6B6B6B' }}>{item.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 表情包预览区域 */}
      <div className="max-w-[960px] mx-auto px-6 py-12 pb-20">
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold mb-2" style={{ color: '#1F1F1F' }}>
            表情包预览
          </h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { day: 'Monday', placeholder: '🖼️' },
            { day: 'Tuesday', placeholder: '🖼️' },
            { day: 'Friday', placeholder: '🖼️' },
          ].map((item, index) => (
            <div 
              key={index}
              className="bg-white rounded-2xl p-4 text-center"
              style={{ border: '1px solid #E8E3D9' }}
            >
              <div 
                className="aspect-square rounded-xl flex items-center justify-center mb-4"
                style={{ backgroundColor: '#F8F6F1' }}
              >
                <span className="text-6xl">{item.placeholder}</span>
              </div>
              <p className="text-sm font-medium" style={{ color: '#1F1F1F' }}>
                打工狗 {item.day}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 第三屏：三步说明 */}
      <div className="max-w-[960px] mx-auto px-6 py-12 pb-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { step: '01', title: '上传照片', desc: '选择你家宠物的可爱照片' },
            { step: '02', title: '自动生成', desc: 'AI 识别并生成打工表情包' },
            { step: '03', title: '下载分享', desc: '直接保存或分享到聊天' },
          ].map((item, index) => (
            <div 
              key={index}
              className="bg-white rounded-2xl p-6 text-center"
              style={{ border: '1px solid #E8E3D9' }}
            >
              <div className="text-5xl font-bold mb-4" style={{ color: '#C98B5F', opacity: 0.3 }}>
                {item.step}
              </div>
              <h3 className="text-lg font-semibold mb-2" style={{ color: '#1F1F1F' }}>
                {item.title}
              </h3>
              <p className="text-sm" style={{ color: '#6B6B6B' }}>
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 text-center">
        <p className="text-sm" style={{ color: '#6B6B6B' }}>
          © AI Company Model Experiment
        </p>
      </footer>
    </div>
  );
}
