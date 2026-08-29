/**
 * Vercel Serverless Function — 文章智能分析
 * 与本地 proxy.py 的 /analyze 路由行为完全一致：
 * 接收 OpenAI 格式请求（api_key + model + messages），
 * 转发到 DeepSeek，原样返回 DeepSeek 的响应
 *
 * 部署后访问：POST /api/analyze
 * api_key 优先取请求体（管理后台「设置」里填写），
 * 未提供时回退到 Vercel 环境变量 DEEPSEEK_API_KEY
 *
 * DeepSeek API 文档：https://platform.deepseek.com/api-docs
 */

export default async function handler(req, res) {
    // 只允许 POST
    if (req.method !== 'POST') {
        return res.status(405).json({ error: '请使用 POST 请求' });
    }

    var body = req.body || {};

    // 密钥来源：前端传来的 api_key > Vercel 环境变量
    var apiKey = String(body.api_key || '').trim() || String(process.env.DEEPSEEK_API_KEY || '').trim();
    if (!apiKey) {
        return res.status(400).json({ error: '缺少 api_key（请在管理后台「设置」里填写 DeepSeek Key）' });
    }

    // 去掉 api_key 字段，其余按 OpenAI 格式原样转发（与 proxy.py 行为一致）
    var payload = Object.assign({}, body);
    delete payload.api_key;

    try {
        var response = await fetch('https://api.deepseek.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + apiKey
            },
            body: JSON.stringify(payload)
        });

        // 原样返回 DeepSeek 的响应（状态码 + 内容），前端解析逻辑与本地代理完全一致
        var text = await response.text();
        res.setHeader('Content-Type', 'application/json');
        return res.status(response.status).send(text);

    } catch (err) {
        console.error('分析失败:', err);
        return res.status(500).json({ error: '分析失败: ' + err.message });
    }
}
