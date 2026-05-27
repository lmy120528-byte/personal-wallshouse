/**
 * 彩虹极坐标点阵呼吸动画
 */
(function () {
    const canvas = document.getElementById('heroBg');
    const ctx = canvas.getContext('2d');

    const TOTAL_RINGS = 14;
    let points = [];
    let baseRadius, centerX, centerY;
    let dpr = window.devicePixelRatio || 1;
    let w, h;
    let startTime = performance.now();

    // ---- Value Noise ----
    function valueNoise(x, y) {
        const ix = Math.floor(x);
        const iy = Math.floor(y);
        const fx = x - ix;
        const fy = y - iy;
        const sx = fx * fx * (3 - 2 * fx);
        const sy = fy * fy * (3 - 2 * fy);

        function hash(ix, iy) {
            let h = ix * 374761393 + iy * 668265263;
            h = (h ^ (h >> 13)) * 1274126177;
            return (h ^ (h >> 16)) / 4294967296 + 0.5;
        }

        const n00 = hash(ix, iy);
        const n10 = hash(ix + 1, iy);
        const n01 = hash(ix, iy + 1);
        const n11 = hash(ix + 1, iy + 1);
        return n00 + (n10 - n00) * sx + (n01 - n00) * sy + (n11 - n10 - n01 + n00) * sx * sy;
    }

    // ---- 生成点阵 ----
    function generatePoints() {
        points = [];
        baseRadius = Math.min(w, h) * 0.22;
        centerX = w / 2;
        centerY = h / 2;
        const ellipseScale = 1 + (w / h - 1) * 0.25;

        for (let ring = 1; ring <= TOTAL_RINGS; ring++) {
            const ringRatio = ring / TOTAL_RINGS;
            const numPts = Math.round(6 * ring * 0.85);

            for (let j = 0; j < numPts; j++) {
                const angle = (j / numPts) * Math.PI * 2;

                points.push({
                    ringRatio: ringRatio,
                    baseAngle: angle,
                    baseR: baseRadius * ringRatio,
                    ellipseScale: ellipseScale
                });
            }
        }
    }

    // ---- 设置画布 ----
    function resize() {
        dpr = window.devicePixelRatio || 1;
        w = window.innerWidth;
        h = window.innerHeight;

        canvas.width = w * dpr;
        canvas.height = h * dpr;
        canvas.style.width = w + 'px';
        canvas.style.height = h + 'px';

        generatePoints();
    }

    let warpedTime = 0;
    let lastNow = 0;

    // ---- 动画帧 ----
    function draw(now) {
        const elapsed = (now - startTime) / 1000;

        // 节奏调制：多组正弦波叠加，产生时快时慢的效果
        const rhythm = 1
            + 0.5 * Math.sin(elapsed * 0.37)
            + 0.35 * Math.sin(elapsed * 0.61 + 1.2)
            + 0.25 * Math.sin(elapsed * 0.23 + 2.8);

        // 将节奏映射为速度系数（0.15 最慢 ~ 2.1 最快）
        const speed = 0.3 + (rhythm + 1.1) / 2.2 * 1.5;

        // 累积 warped time（帧间时间差 × 速度系数）
        if (lastNow > 0) {
            const dt = (now - lastNow) / 1000;
            warpedTime += dt * speed;
        }
        lastNow = now;

        ctx.clearRect(0, 0, w * dpr, h * dpr);

        const t = warpedTime; // 用 warped time 驱动所有运动

        for (let i = 0; i < points.length; i++) {
            const p = points[i];

            // noise 输入
            const nx = Math.cos(p.baseAngle) * p.ringRatio + t * 0.18;
            const ny = Math.sin(p.baseAngle) * p.ringRatio + t * 0.18;
            const n = valueNoise(nx, ny);

            // 半径扰动
            const r = p.baseR * (1 + n * 0.28);

            // 角度微偏转
            const angleOffset = (valueNoise(nx + 100, ny + 100) - 0.5) * 0.5;
            const angle = p.baseAngle + angleOffset;

            // 坐标
            const x = centerX + Math.cos(angle) * r * p.ellipseScale;
            const y = centerY + Math.sin(angle) * r;

            // 颜色
            const hue = ((p.baseAngle / (Math.PI * 2)) * 360 + t * 8) % 360;
            const lightness = 55 + (valueNoise(nx + 200, ny + 200) - 0.5) * 20;

            // 透明度
            const edgeFade = 1 - Math.pow(p.ringRatio, 1.8);
            const alphaNoise = (valueNoise(nx + 300, ny + 300) - 0.5) * 0.6;
            const alpha = Math.max(0, Math.min(1, edgeFade + alphaNoise));

            // 点的大小：1.5 ~ 2.5px
            const dotR = (1.5 + p.ringRatio * 1.0) * dpr;

            // 绘制
            ctx.beginPath();
            ctx.arc(x * dpr, y * dpr, dotR, 0, Math.PI * 2);
            ctx.fillStyle = `hsla(${hue}, 100%, ${lightness}%, ${alpha})`;
            ctx.fill();
        }

        requestAnimationFrame(draw);
    }

    // ---- 启动 ----
    resize();
    startTime = performance.now();
    window.addEventListener('resize', () => {
        resize();
        startTime = performance.now();
        warpedTime = 0;
        lastNow = 0;
    });
    requestAnimationFrame(draw);
})();
