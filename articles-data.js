/**
 * 文章数据中心
 * 新增文章：在数组中加一条记录即可，GitHub push 后 Vercel 自动更新
 */
var articles = [

    // ===== GEO 实战 =====
    {
        series: 'geo',
        seriesName: 'GEO 实战',
        title: 'GEO做法解析——两端一连接',
        date: '2026-05-17',
        summary: 'GEO优化需从传统SEO转向“两端一连接”框架：品牌端构建模型可理解的结构化内容资产，模型端理解AI认知逻辑，连接端布局多源可交叉验证的信息网络。',
        wordCount: 3600,
        readingTime: 14,
        tags: ["GEO优化","两端一连接"],
        url: 'https://mp.weixin.qq.com/s/QOC8w1hSxbkbHdAgQY7qDw'
    },
    {
        series: 'geo',
        seriesName: 'GEO 实战',
        title: 'GEO 行业定位——三维定位模型',
        date: '2026-05-17',
        summary: '提出GEO行业定位的三维模型：模型/用户分层、行业/场景分层、品牌/规模分层，帮助品牌根据自身坐标选择差异化优化策略。',
        wordCount: 3600,
        readingTime: 14,
        tags: ["GEO优化","三维定位模型"],
        url: 'https://mp.weixin.qq.com/s/W-uFfKJYLwR-jtKOq8D8vw'
    },
    {
        series: 'geo',
        seriesName: 'GEO 实战',
        title: 'GEO，AI时代品牌"认知体"构建过程',
        date: '2026-05-17',
        summary: 'GEO不是在AI时代做SEO，而是为品牌构建可被模型理解的"认知体"。文章系统梳理了行业两种路线、四类服务商格局，提出"两端一连接"落地框架，最终指向品牌Agent作为行业终局。',
        wordCount: 5500,
        readingTime: 22,
        tags: ["GEO认知体","品牌Agent"],
        url: 'https://mp.weixin.qq.com/s/sUgA3lK6pUNyOQGY4J_PhA'
    },
    {
        series: 'geo',
        seriesName: 'GEO 实战',
        title: '如何让你的内容被 AI 搜索引用：三条核心原则',
        date: '2025-01-15',
        summary: '基于一线实操经验，总结出让 AI 搜索引擎更愿意引用你内容的三条关键原则和实操技巧。',
        wordCount: 2800,
        readingTime: 11,
        tags: ["GEO","AI搜索","内容优化"],
        url: 'https://mp.weixin.qq.com/s/sUgA3lK6pUNyOQGY4J_PhA'
    },
    {
        series: 'geo',
        seriesName: 'GEO 实战',
        title: 'GEO 与传统 SEO 的本质区别：思维模式的转变',
        date: '2025-01-10',
        summary: '为什么用传统 SEO 的思维做 GEO 行不通？深入分析两种范式的底层逻辑差异与应对策略。',
        wordCount: 3500,
        readingTime: 14,
        tags: ["GEO","SEO","思维模式"],
        url: 'https://mp.weixin.qq.com/s/sUgA3lK6pUNyOQGY4J_PhA'
    },
    {
        series: 'geo',
        seriesName: 'GEO 实战',
        title: '实战复盘：一次 GEO 策略调整带来的 3 倍流量增长',
        date: '2025-01-05',
        summary: '记录一次完整的 GEO 策略调整过程，从问题诊断、方案设计到效果验证的全链路实操复盘。',
        wordCount: 4100,
        readingTime: 16,
        tags: ["GEO","复盘","增长"],
        url: 'https://mp.weixin.qq.com/s/sUgA3lK6pUNyOQGY4J_PhA'
    },

    // ===== 白话 AI =====
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: 'RAG是什么·有什么用途',
        date: '2026-06-05',
        summary: 'RAG（检索增强生成）通过检索外部文档辅助大模型回答，解决知识固化、幻觉和领域专业性问题，核心流程包括文档切片、向量化、存储和检索。',
        wordCount: 2200,
        readingTime: 9,
        tags: ["RAG技术","文档切片策略"],
        url: 'https://mp.weixin.qq.com/s/NBX1D4V4y6fNZ-xjvLm_Xw'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: 'Agent 概念祛魅：从 MCP 到 Harness，所有术语背后的本质逻辑',
        date: '2026-05-31',
        summary: 'AI Agent领域所有概念（Prompt工程、Function Calling、MCP、工作流、Skill、Harness工程）本质上是解决“降低人类参与度”这一主线问题的阶段性方案，核心在于用工程化手段驾驭大模型智能。',
        wordCount: 2600,
        readingTime: 10,
        tags: ["AI Agent","Harness工程"],
        url: 'https://mp.weixin.qq.com/s/8GvVjCCnv1PyuTqmgCMnmA'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: '用户研究中的定量与定性',
        date: '2026-05-03',
        summary: '用户研究方法分为定性研究（解决“怎么想”）和定量研究（解决“怎么做”），两者可结合验证，如用户访谈与A/B测试的配合。',
        wordCount: 1600,
        readingTime: 6,
        tags: ["用户研究方法","定性与定量"],
        url: 'https://mp.weixin.qq.com/s/o4dX0aSN_35NeI6ozcV_Gw'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: '什么是大语言模型？用做菜来理解 LLM 的原理',
        date: '2025-01-20',
        summary: '不用任何术语，用"做菜"这个生活场景帮你理解大语言模型到底是怎么工作的。',
        wordCount: 2200,
        readingTime: 9,
        tags: ["LLM","科普","AI基础"],
        url: 'https://mp.weixin.qq.com/s/sUgA3lK6pUNyOQGY4J_PhA'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: 'Prompt 不是咒语：三分钟搞懂提示词的本质',
        date: '2025-01-18',
        summary: '为什么有些人的 Prompt 效果好、有些不行？揭开提示词的神秘面纱，用大白话讲清楚原理。',
        wordCount: 1800,
        readingTime: 7,
        tags: ["Prompt","提示词","科普"],
        url: 'https://mp.weixin.qq.com/s/sUgA3lK6pUNyOQGY4J_PhA'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: 'Agent 到底是什么？不是魔法，是"会动手的 AI"',
        date: '2025-01-12',
        summary: 'Agent 是当下 AI 圈最热的概念之一，但它不是魔法。用通俗的方式解释 Agent 的核心原理与应用场景。',
        wordCount: 2600,
        readingTime: 10,
        tags: ["Agent","AI应用","科普"],
        url: 'https://mp.weixin.qq.com/s/sUgA3lK6pUNyOQGY4J_PhA'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: 'Embedding 嵌入：让机器"理解"词语之间的关系',
        date: '2025-01-08',
        summary: '"词语变成数字就能让机器理解含义？"用最简单的例子讲清楚 Embedding 这个 AI 领域的基础概念。',
        wordCount: 2000,
        readingTime: 8,
        tags: ["Embedding","NLP","科普"],
        url: 'https://mp.weixin.qq.com/s/sUgA3lK6pUNyOQGY4J_PhA'
    }

];
