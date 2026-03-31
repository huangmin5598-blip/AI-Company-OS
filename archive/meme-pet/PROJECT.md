# 表情包生成 MVP 项目

## 项目概述
- **项目名称**: meme-pet
- **类型**: Next.js 全栈 Web 应用
- **核心功能**: 用户上传宠物照片，一键生成九宫格表情包
- **目标用户**: 养宠物的主人，想把宠物做成表情包

## 技术栈
- Next.js 14 (App Router)
- TypeScript
- sharp (图像处理)
- remove.bg API (抠图)
- Vercel (部署)

## 核心功能清单

### P0 - 必须做
1. **上传页面** (`/`)
   - 拖拽/选择图片上传
   - 支持 image/*, <=10MB
   - 伪进度条动画

2. **生成 API** (`/api/generate`)
   - 接收 multipart/form-data: file + theme
   - 使用 remove.bg API 抠图
   - 用 sharp 把抠图结果叠加到 9 张模板
   - 拼成九宫格 PNG
   - 返回 { id }

3. **结果页** (`/r/[id]`)
   - 展示九宫格预览
   - 下载按钮
   - 复制分享链接
   - 竖版封面（小红书用）
   - "今日第 N 只" 计数

4. **模板系统**
   - 模板目录: `lib/templates/<theme>/`
   - 1-9.png (9张模板)
   - layout.json (位置配置)
   - 当前默认主题: workdog (打工狗)

### P1 - 应该做
- 案例墙
- 分享 ref 统计
- 缓存去重

## 目录结构
```
meme-pet/
├── app/
│   ├── api/
│   │   ├── generate/route.ts    # 生成入口
│   │   └── result/[id]/route.ts  # 获取结果
│   ├── r/
│   │   └── [id]/page.tsx         # 结果页
│   ├── page.tsx                  # 首页/上传页
│   └── layout.tsx
├── lib/
│   ├── removebg.ts               # remove.bg 封装
│   ├── compose.ts                # sharp 合成
│   ├── templates/workdog/        # 打工狗模板
│   │   ├── 1.png ~ 9.png
│   │   └── layout.json
│   └── store.ts                  # 存储 (临时文件)
├── public/
├── package.json
└── .env.local
```

## 环境变量
```
REMOVEBG_API_KEY=你的remove.bg_api_key
```

## 关键代码逻辑

### 1. 抠图 + 合成流程
1. 接收用户上传的图片
2. 调用 remove.bg API 抠图（返回透明背景 PNG）
3. 读取模板目录的 9 张模板图
4. 用 sharp 把抠图叠加到每张模板的指定位置
5. 拼成 3x3 九宫格
6. 添加水印
7. 保存并返回 ID

### 2. layout.json 格式
```json
{
  "width": 600,
  "height": 600,
  "overlays": [
    { "x": 50, "y": 100, "width": 200, "height": 200 }
  ]
}
```

## 部署
- Vercel (前端 + API)
- 临时存储用 /tmp，上线后改 R2/S3

---

## 你的任务
1. 初始化 Next.js 项目
2. 安装依赖 (sharp, remove.bg)
3. 实现所有 P0 功能
4. 创建默认模板（打工狗）
5. 配置环境变量
6. 部署到 Vercel

开始吧！