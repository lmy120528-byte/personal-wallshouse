/**
 * 文章数据中心
 * 新增文章：在数组中加一条记录即可，GitHub push 后 Vercel 自动更新
 */
var articles = [

    // ===== GEO 实战 =====
    {
        series: 'geo',
        seriesName: 'GEO 实战',
        title: 'GEO 需要一场“信任革命”：如何为 AI 时代搭建品牌信息的“安全声明”',
        date: '2026-08-11',
        summary: 'GEO行业陷入内容投喂的负和博弈，作者提出从\'外部扰动\'转向\'成为基础事实层\'的范式转移，通过数据原子化、区块链存证、去中心化验证和链上声誉构建AI可信的品牌信息基础设施，实现从抢排名到建画像的升维。',
        wordCount: 6600,
        readingTime: 27,
        tags: ["GEO优化","信任机制"],
        url: 'https://mp.weixin.qq.com/s/zG6JkTmc4ZFQUVZjf3xq3A'
    },
    {
        series: 'geo',
        seriesName: 'GEO 实战',
        title: '别把 GEO 做成 AI 版 SEO：它的终局是共生，不是对抗',
        date: '2026-06-18',
        summary: 'GEO不是AI版的SEO，其核心是与AI平台共生，通过标准化品牌信息帮助平台完善供给，而非钻空子抢流量。',
        wordCount: 1900,
        readingTime: 7,
        tags: ["GEO优化","AI生态"],
        url: 'https://mp.weixin.qq.com/s/OmQ_tsaqZ6v-dQvoBSI3lg'
    },
    {
        series: 'geo',
        seriesName: 'GEO 实战',
        title: 'GEO 的三次跃迁：行业的边界，从来都是 AI 平台画的',
        date: '2026-06-18',
        summary: 'GEO的边界由AI平台进化阶段决定：从信息分发的品牌可见性，到服务触达的线索获客，再到交易闭环的转化成交，服务商需跟随平台生态升级能力。',
        wordCount: 1400,
        readingTime: 6,
        tags: ["GEO进化","AI平台生态"],
        url: 'https://mp.weixin.qq.com/s/Fi2-Rt8Z8IUFg22tHp3gMw'
    },
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

    // ===== 白话 AI =====
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: 'Agent 比我做得好，我为什么不敢放手？',
        date: '2026-10-11',
        summary: '传统产品经理面对Agent时产生失控感，源于思考维度从执行细节位移到意图架构与边界设定，人应守住方向判断与最终裁决权。',
        wordCount: 2200,
        readingTime: 9,
        tags: ["Agent协作","产品经理转型"],
        url: 'https://mp.weixin.qq.com/s/wIqoxG50vXb4VwvibC62Rw'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: 'DeepSeek Harness 机制初探：三个心智模型，搞懂 Agent 时代的「操作系统」',
        date: '2026-08-10',
        summary: 'DeepSeek Harness 是面向 AI Agent 的插件化运行时操作系统，用插件树、叠层配置、流水线三个心智模型讲清其底层机制。',
        wordCount: 5500,
        readingTime: 22,
        tags: ["Agent操作系统","插件化架构"],
        url: 'https://mp.weixin.qq.com/s/qOdSbTmyp3oJ2FQKq9ek0A'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: 'AI 时代的产品设计-在不确定的基座上寻求秩序',
        date: '2026-07-21',
        summary: 'AI时代产品设计从画路径转向设护栏，核心是区分哪些不确定性必须压制、哪些可以释放，并建立自动化评估体系。',
        wordCount: 1700,
        readingTime: 7,
        tags: ["AI产品设计","不确定性管理"],
        url: 'https://mp.weixin.qq.com/s/KtBexYv-1Dcsc4Bz7-8uzQ'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: '产品经理用 VibeCoding搭建个人网站 系列（1）',
        date: '2026-06-28',
        summary: '产品经理用VibeCoding搭建个人网站，通过Claude Code、GitHub、Vercel、Render四个工具实现零成本部署，并构建基于RAG的数字分身Agent，强调AI时代产品经理需理解技术边界并引导模型。',
        wordCount: 3300,
        readingTime: 13,
        tags: ["VibeCoding","数字分身Agent"],
        url: 'https://mp.weixin.qq.com/s/gIy72m_sUte1bE1n5KMS5A'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: 'Eval 评估：如何定义问题集的评估维度',
        date: '2026-06-14',
        summary: 'Eval评估中，评分维度并非适用于所有问题，需基于Agent工作流定义问题与评分维度的映射，避免主观臆测。',
        wordCount: 1900,
        readingTime: 8,
        tags: ["Eval评估","评分维度映射"],
        url: 'https://mp.weixin.qq.com/s/T5ekoT6DUw5Qu_RD4tTqog'
    },
    {
        series: 'ai',
        seriesName: '白话 AI',
        title: 'AI 产品中的 Eval 评估体系是什么',
        date: '2026-06-11',
        summary: 'Evals评估体系是AI产品的质量保障基础设施，通过定义评分规则、设计评测集、设定合格阈值和分析Badcase，建立可量化、可重复、可迭代的效果验证与调优机制，解决AI产品“没有绝对正确答案”下的质量判断问题。',
        wordCount: 3600,
        readingTime: 14,
        tags: ["Evals评估体系","AI产品质量保障"],
        url: 'https://mp.weixin.qq.com/s/5xBLkA2dqWXtEHBhmbU_zw'
    },
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
    }

];
