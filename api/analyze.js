/**
 * Vercel Serverless Function — 文章智能分析
 * 接收文章全文，调用 DeepSeek 生成摘要和标签
 *
 * 部署后访问：POST /api/analyze
 * 需要在 Vercel 设置环境变量 DEEPSEEK_API_KEY
 *
 * DeepSeek API 文档：https://platform.deepseek.com/api-docs
 */

// 系统提示词：告诉模型它的角色和输出格式
var SYSTEM_PROMPT = [
    '你是专业内容编辑助手，为技术文章写摘要和标签。',
    '',
    '为每篇文章生成：',
    '1. 摘要（summary）：1-2句话概括文章核心内容，不超过80字，直击要点，中文',
    '2. 标签（tags）：1-2个精准标签，根据文章实际内容提炼，用简洁的中文短语',
    '',
    '标签要求：',
    '- 从文章中提取最核心的关键词作为标签，如"GEO优化"、"Prompt设计"等',
    '- 标签要具体、有辨识度，不要用太宽泛的词如"技术"、"方法"',
    '- 严格1-2个，宁少勿多',
    '',
    '摘要要求：不要写"本文介绍了..."这样的开头，直接说核心观点',
    '',
    '只返回JSON数组，不要任何markdown标记或额外文字。',
    '格式：[{"summary": "...", "tags": ["标签1", "标签2"]}, ...]'
].join('\n');

export default async function handler(req, res) {
    // 只允许 POST
    if (req.method !== 'POST') {
        return res.status(405).json({ error: '请使用 POST 请求' });
    }

    var articles = req.body?.articles;

    if (!articles || !Array.isArray(articles) || articles.length === 0) {
        return res.status(400).json({ error: '请提供 articles 数组' });
    }

    // 构建用户消息：列出所有待分析文章
    var articlesText = articles.map(function (a, i) {
        return '【文章 ' + (i + 1) + '】\n标题：' + (a.title || '无标题') + '\n全文：\n' + a.content + '\n';
    }).join('\n---\n\n');

    var userPrompt = '请为以下 ' + articles.length + ' 篇文章生成摘要和标签：\n\n' + articlesText + '\n请以 JSON 数组格式返回（只返回 JSON，不要其他文字）：\n[{"summary": "摘要1", "tags": ["标签A", "标签B"]}, {"summary": "摘要2", "tags": ["标签C"]}, ...]';

    try {
        // 调用 DeepSeek API（兼容 OpenAI 格式）
        var response = await fetch('https://api.deepseek.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + process.env.DEEPSEEK_API_KEY
            },
            body: JSON.stringify({
                model: 'deepseek-chat',
                temperature: 0.3,          // 低温度，保证输出稳定
                max_tokens: 2000,
                messages: [
                    { role: 'system', content: SYSTEM_PROMPT },
                    { role: 'user', content: userPrompt }
                ]
            })
        });

        if (!response.ok) {
            var errText = '';
            try { errText = await response.text(); } catch (e) {}
            console.error('DeepSeek API 错误:', response.status, errText);
            return res.status(502).json({ error: 'AI 分析服务异常（' + response.status + '），请稍后重试' });
        }

        var data = await response.json();
        var text = data.choices[0].message.content;

        // 解析 DeepSeek 返回的 JSON（去掉可能的 markdown 标记）
        var jsonStr = text.replace(/```json\s*/g, '').replace(/```\s*/g, '').trim();
        var results = JSON.parse(jsonStr);

        return res.status(200).json({ results: results });

    } catch (err) {
        console.error('分析失败:', err);
        return res.status(500).json({ error: '分析失败: ' + err.message });
    }
}
