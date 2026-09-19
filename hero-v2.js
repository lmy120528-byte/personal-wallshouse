/**
 * Hero 动效 V2 —— 完整版（参考 youziailab.design 的实现重写）
 *
 * 三层结构（由下至上）：
 *   ① WebGL 彩虹环（GPU shader）：细环 + 三层辉光（核心亮带 / 外圈光晕 / 白色高光）
 *   ② 粒子点阵（Canvas 2D）：全屏均匀网格，波纹从中心向外传播，波经过的点被推开/旋转/点亮
 *   ③ 文字 + 遮罩（HTML/CSS，不变）
 *
 * 节奏编排（GSAP，4.6 秒循环）：
 *   大环：快升 1.0s → 保持 0.8s → 淡出 0.8s，同时第二环扩散→急收（0.7s），
 *         第三环在第 2.6s 缓缓展开 1.3s → 急收，阶段长短不一 → "忽快忽慢"
 *   粒子：同频呼吸，点阵波纹周期 4.2s，与 4.6s 循环轻微失谐 → 每轮图案略有不同，不死板
 *
 * 降级保护：THREE 缺失 / WebGL 不支持 → 只跑点阵；gsap 缺失 → 正弦波模拟
 * 性能：hero 滚出屏幕暂停渲染；渲染精度上限 2x
 */
(function () {
    'use strict';

    // ============ 全局速度旋钮 ============
    // 1 = 原速，0.8 = 放慢 20%。同时作用于 GSAP 时间线、粒子波纹、shader 流光，
    // 三个时钟同比例缩放，节奏关系（含刻意设计的失谐）保持不变
    var SPEED = 0.8;

    // ============ 公共状态（GSAP 时间线持续写入，渲染循环每帧读取） ============

    // WebGL 环：ring1 由 strength 驱动；ring2/3 由各自的 scale/opacity 驱动
    var ringStrength = 0;
    var ring2Scale = 0, ring2Opacity = 0;
    var ring3Scale = 0, ring3Opacity = 0;

    // 粒子点阵的呼吸主值
    var particleStrength = 0;

    var dotCanvas = document.getElementById('heroBg');

    // ============ 模块一：WebGL 彩虹环（shader 在显卡上每像素并行计算） ============

    function createWaveRing(wrapper) {
        var testCanvas = document.createElement('canvas');
        var glOk = !!(testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl'));
        if (!glOk || typeof THREE === 'undefined') return null;

        var scene = new THREE.Scene();
        // 正交相机：2D 全屏效果无透视变形
        var camera = new THREE.OrthographicCamera(-0.5, 0.5, 0.5, -0.5, -1000, 1000);
        camera.position.set(0, 0, 2);

        var renderer = new THREE.WebGLRenderer({ alpha: false, antialias: true });
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setClearColor(0x030209, 1);
        wrapper.appendChild(renderer.domElement);

        var vertexShader = [
            'varying vec2 vUv;',
            'void main() {',
            '  vUv = uv;',
            '  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);',
            '}'
        ].join('\n');

        var fragmentShader = [
            'precision mediump float;',
            'uniform float time;',
            'uniform float strength;',
            'uniform float ring2Scale; uniform float ring2Opacity;',
            'uniform float ring3Scale; uniform float ring3Opacity;',
            'uniform vec2 uResolution;',
            'varying vec2 vUv;',
            '',
            'float hash(vec2 p) {',
            '  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);',
            '}',
            '',
            '// 环的渲染：三层叠加',
            '//  ringBright  = 核心细亮带（smoothstep 窄带）',
            '//  innerShadow = 带内暗影，增加立体感',
            '//  outerGlow   = 外圈光晕（宽 4 倍），柔和发散',
            '//  outerBright = 白色高光（pow 1.8 收紧），像能量环',
            'vec3 buildRing(float dist, float pos, float width, float ringOpacity, vec2 centeredUV) {',
            '  float ringBright = (pos < 0.01) ? 0.0',
            '    : 1.0 - smoothstep(0.0, width, abs(dist - pos));',
            '  float innerShadow = (pos < 0.01) ? 0.0',
            '    : 1.0 - smoothstep(width, width * 1.5, abs(dist - pos));',
            '  float outerBright = pow(ringBright, 1.8);',
            '  float outerGlow = (pos < 0.01) ? 0.0',
            '    : 1.0 - smoothstep(0.0, width * 4.0, abs(dist - pos));',
            '',
            '  // 色相 = 圆周角度，彩虹沿环完整走一圈',
            '  float angle = atan(centeredUV.y, centeredUV.x);',
            '  float hue = angle / 6.28318 + 0.5;',
            '  vec3 rainbow = vec3(',
            '    abs(fract(hue + 0.0)  * 6.0 - 3.0) - 1.0,',
            '    abs(fract(hue + 0.33) * 6.0 - 3.0) - 1.0,',
            '    abs(fract(hue + 0.67) * 6.0 - 3.0) - 1.0',
            '  );',
            '  rainbow = clamp(rainbow, 0.0, 1.0);',
            '',
            '  vec3 c = vec3(0.0);',
            '  c += rainbow * ringBright  * ringOpacity * 1.8;',
            '  c += rainbow * outerGlow   * ringOpacity * 0.35;',
            '  c += vec3(1.0) * outerBright * ringOpacity * 0.5;',
            '  c *= 0.6 + innerShadow * 0.4;',
            '  return c;',
            '}',
            '',
            'void main() {',
            '  vec2 aspect = vec2(uResolution.x / uResolution.y, 1.0);',
            '  vec2 centeredUV = (vUv - 0.5) * aspect;',
            '  float dist = length(centeredUV);',
            '',
            '  // ---- Ring 1：strength 驱动，快升 → 保持 → 淡出 ----',
            '  float wave1 = pow(strength, 0.6);',
            '  float pos1 = wave1 * 0.89;',
            '  float w1 = 0.006 + strength * 0.004;   // 细！0.006~0.01',
            '  float fade1 = 1.0 - smoothstep(0.28, 0.89, dist);',
            '  vec3 ring1Color = buildRing(dist, pos1, w1, fade1, centeredUV);',
            '',
            '  // ---- Ring 2：扩散 → 急收，透明度随收回归零 ----',
            '  float pos2 = ring2Scale * 0.89;',
            '  float w2 = 0.007 + ring2Scale * 0.003;',
            '  float fade2 = 1.0 - smoothstep(0.0, 0.89, dist);',
            '  vec3 ring2Color = buildRing(dist, pos2, w2, fade2 * ring2Opacity, centeredUV);',
            '',
            '  // ---- Ring 3：同 Ring 2，直径小 15% ----',
            '  float pos3 = ring3Scale * 0.89 * 0.85;',
            '  float w3 = 0.007 + ring3Scale * 0.003;',
            '  float fade3 = 1.0 - smoothstep(0.0, 0.89, dist);',
            '  vec3 ring3Color = buildRing(dist, pos3, w3, fade3 * ring3Opacity, centeredUV);',
            '',
            '  // ---- 背景：深蓝黑 + 对角扫光 + 中心辉光 + 微光闪烁 ----',
            '  vec3 baseColor = vec3(0.012, 0.008, 0.035);',
            '',
            '  float sweep = pow(sin(vUv.x + vUv.y - time * 0.18) * 0.5 + 0.5, 14.0) * strength * 0.14;',
            '  baseColor += vec3(sweep * 0.7, sweep * 0.8, sweep * 1.0);',
            '',
            '  float radialGlow = smoothstep(0.65, 0.0, dist) * 0.09 * strength;',
            '  baseColor += vec3(radialGlow * 0.6, radialGlow * 0.7, radialGlow * 1.0);',
            '',
            '  float shimmer = sin(vUv.y * 3.0 + time * 0.15) * 0.003 * strength;',
            '  baseColor += vec3(shimmer * 0.5, shimmer * 0.7, shimmer * 1.0);',
            '',
            '  // ---- 合成：背景 + 三个环 ----',
            '  vec3 color = baseColor;',
            '  float ringMix = clamp(',
            '    ((pos1 < 0.01) ? 0.0 : 1.0 - smoothstep(0.0, 0.006 + strength * 0.004, abs(dist - pos1))) * fade1',
            '    + ((pos2 < 0.01) ? 0.0 : 1.0 - smoothstep(0.0, 0.007 + ring2Scale * 0.003, abs(dist - pos2))) * fade2 * ring2Opacity * 0.5',
            '    + ((pos3 < 0.01) ? 0.0 : 1.0 - smoothstep(0.0, 0.007 + ring3Scale * 0.003, abs(dist - pos3))) * fade3 * ring3Opacity * 0.5,',
            '    0.0, 1.0',
            '  );',
            '  color = mix(color, ring1Color + ring2Color + ring3Color, ringMix);',
            '  color += vec3(1.0) * pow(ringMix, 3.0) * 0.2;',
            '',
            '  // 抖动噪声：防暗部色带',
            '  float dither = hash(vUv + mod(time, 100.0)) * 0.004 - 0.002;',
            '  color.rgb += dither;',
            '',
            '  gl_FragColor = vec4(clamp(color, 0.0, 1.0), 1.0);',
            '}'
        ].join('\n');

        var uniforms = {
            time: { value: 0 },
            strength: { value: 0 },
            ring2Scale: { value: 0 },
            ring2Opacity: { value: 0 },
            ring3Scale: { value: 0 },
            ring3Opacity: { value: 0 },
            uResolution: { value: new THREE.Vector2(1, 1) }
        };

        var material = new THREE.ShaderMaterial({
            uniforms: uniforms,
            vertexShader: vertexShader,
            fragmentShader: fragmentShader
        });

        var mesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), material);
        scene.add(mesh);

        function resize() {
            var w = wrapper.clientWidth;
            var h = wrapper.clientHeight;
            renderer.setSize(w, h);
            uniforms.uResolution.value.set(w, h);
        }
        resize();
        window.addEventListener('resize', resize);

        function tick() {
            // time 乘 SPEED：shader 里的扫光、闪烁与 GSAP 同比例放慢
            uniforms.time.value = performance.now() * 0.001 * SPEED;
            uniforms.strength.value = ringStrength;
            uniforms.ring2Scale.value = ring2Scale;
            uniforms.ring2Opacity.value = ring2Opacity;
            uniforms.ring3Scale.value = ring3Scale;
            uniforms.ring3Opacity.value = ring3Opacity;
            renderer.render(scene, camera);
        }

        return { tick: tick, resize: resize };
    }

    // ============ 模块二：粒子点阵（全屏网格 + 波纹传播） ============

    function createParticles(canvas) {
        if (!canvas) return null;
        var ctx = canvas.getContext('2d');

        var SPACING = 14;      // 网格间距（px）
        var DOT_R = 1.5;       // 点的基础半径
        var PERIOD = 4.2;      // 波纹传播周期（秒），与 4.6s 呼吸循环轻微失谐
        var PI2 = Math.PI * 2;

        var cols, rows, count;
        var dpr = 1, w = 0, h = 0;
        var baseX, baseY, dist;

        // ---- 预渲染 360 个色相精灵：启动时画好 360 张径向渐变小图，
        //      每帧直接贴图，避免每帧几百次 createRadialGradient + 字符串拼接 ----
        var colorSprites = [];
        for (var hue = 0; hue < 360; hue++) {
            var sprite = document.createElement('canvas');
            sprite.width = sprite.height = 32;
            var sctx = sprite.getContext('2d');
            var g = sctx.createRadialGradient(16, 16, 0, 16, 16, 16);
            g.addColorStop(0, 'hsla(' + hue + ', 100%, 62%, 1)');
            g.addColorStop(0.45, 'hsla(' + hue + ', 100%, 56%, 1)');
            g.addColorStop(1, 'hsla(' + hue + ', 100%, 52%, 0)');
            sctx.fillStyle = g;
            sctx.fillRect(0, 0, 32, 32);
            colorSprites.push(sprite);
        }

        function drawRainbowDot(x, y, size, hue) {
            var idx = Math.floor(((hue % 360) + 360) % 360);
            var sprite = colorSprites[idx];
            if (sprite) {
                ctx.drawImage(sprite, x - size, y - size, size * 2, size * 2);
            }
        }

        // 正弦软化的近似方波：波经过时 smooth 地推拉，而不是突跳
        function rsw(t, delta) {
            return (0.25465 / Math.PI) * 2 * Math.atan(Math.sin(PI2 * t / PERIOD) / delta);
        }

        // smoothstep S 曲线（提到循环外，避免每帧重复创建函数）
        function smoothstep(x) { return x * x * (3 - 2 * x); }

        var R_OUTER = function () { return w * 0.25; }; // 呼吸外环半径 = 宽度的 1/4

        function buildGrid() {
            var sx = w / (cols - 1), sy = h / (rows - 1);
            for (var i = 0; i < count; i++) {
                var col = i % cols, row = ~~(i / cols);
                var x = col * sx + (Math.random() - 0.5) * sx * 0.3;
                var y = row * sy + (col % 2) * sy * 0.5 + (Math.random() - 0.5) * sy * 0.3;
                baseX[i] = x;
                baseY[i] = y;
                var dx = x - w * 0.5, dy = y - h * 0.5;
                // 8 角星扰动：打破网格的机械规则感
                dist[i] = Math.sqrt(dx * dx + dy * dy) + Math.cos(Math.atan2(dy, dx) * 8) * sx * 0.8;
            }
        }

        function resize() {
            var rect = canvas.parentElement.getBoundingClientRect();
            dpr = Math.min(window.devicePixelRatio || 1, 2);
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
            w = rect.width;
            h = rect.height;
            cols = Math.max(20, Math.round(w / SPACING));
            rows = Math.max(12, Math.round(h / SPACING));
            count = cols * rows;
            baseX = new Float32Array(count);
            baseY = new Float32Array(count);
            dist = new Float32Array(count);
            buildGrid();
        }
        resize();

        function draw() {
            // t 乘 SPEED：波纹传播周期与 GSAP 呼吸同比例放慢
            var t = performance.now() * 0.001 * SPEED;
            // 粒子中心略偏右（与视觉重心对齐），呼吸半径随 GSAP strength 扩缩
            var cx = w * 0.52, cy = h * 0.5;
            var outerR = R_OUTER();
            var innerR = outerR * 0.5;
            var R_now = innerR + (outerR - innerR) * particleStrength;
            var maxDist = outerR;

            ctx.clearRect(0, 0, w, h);

            for (var i = 0; i < count; i++) {
                var bx = baseX[i], by = baseY[i], d = dist[i];

                // 波纹：相位 = 时间 - 距离/传播速度（300px/s）→ 波从中心向外扫过点阵
                // delta 随距离增大 → 远处的波更圆润
                var wave = rsw(t - d / 300, 0.15 + (0.2 * d) / (maxDist * 0.8)) * particleStrength;

                // 波经过处：点被"推开"（scale）并"旋开"（rot，最大 90°，边缘衰减）
                var dx = bx - cx, dy = by - cy;
                var scale = wave + 1.8;
                var rot = wave * 1.5708 * (1 - Math.min(d / maxDist, 1));
                var cos = Math.cos(rot), sin = Math.sin(rot);
                var px = cx + (dx * cos - dy * sin) * scale;
                var py = cy + (dx * sin + dy * cos) * scale;

                if (px < -20 || px > w + 20 || py < -20 || py > h + 20) continue;

                // 暗角：以当前呼吸半径 R_now 为界平滑淡出（smoothstep S 曲线）
                var rawDist = Math.sqrt((px - cx) * (px - cx) + (py - cy) * (py - cy));
                var vignette = 1 - smoothstep(Math.min(rawDist / R_now, 1));

                var alpha = 0.96 + 0.04 * (1 - Math.min(rawDist / (maxDist * 0.92), 1)) + wave * 0.04;
                var combinedAlpha = Math.min(1, alpha) * vignette;
                if (combinedAlpha < 0.01) continue;

                // 波经过时点变大
                var sz = DOT_R * (0.6 + (wave + 0.4) * 0.8) * 2.5;

                // 色相绕圆心角度映射，红橙黄绿蓝靛紫走满 360°
                var angle = Math.atan2(py - cy, px - cx);
                var hue = ((angle + Math.PI) / PI2) * 360;

                ctx.globalAlpha = combinedAlpha;
                drawRainbowDot(px, py, sz, hue);
                ctx.globalAlpha = 1;
            }
        }

        window.addEventListener('resize', resize);

        return { draw: draw, resize: resize };
    }

    // ============ 模块三：GSAP 编排（4.6 秒循环，阶段长短不一 = 忽快忽慢） ============

    function startTimeline() {
        var PI2_SIN = Math.PI * 2;
        if (typeof gsap === 'undefined') {
            // 降级：gsap 没加载成功，用正弦波模拟
            return function () {
                var t = performance.now() * 0.001;
                var s = (Math.sin(t * SPEED * (PI2_SIN / 4.6) - Math.PI / 2) + 1) / 2;
                ringStrength = s;
                particleStrength = s;
            };
        }

        // ---- WebGL 环时间线 ----
        // Ring1 快升(1.0s) → 保持(0.8s) → 淡出(0.8s)
        // Ring2 在淡出同时扩散(0.8s) → 急收(0.7s，与前一段重叠 0.5s)
        // Ring3 在第 2.6s 缓缓展开(1.3s) → 急收(0.7s，重叠 0.5s)
        // 总长 4.6s，repeat: -1 无缝循环
        var strengthProxy = { v: 0 };
        var r2Proxy = { v: 0 };
        var r3Proxy = { v: 0 };

        gsap.timeline({ repeat: -1, timeScale: SPEED })
            // Ring 1：快升
            .to(strengthProxy, {
                v: 1, duration: 1.0, ease: 'power2.out',
                onUpdate: function () { ringStrength = strengthProxy.v; }
            })
            // Ring 1：保持
            .to(strengthProxy, {
                v: 1, duration: 0.8, ease: 'none',
                onUpdate: function () { ringStrength = strengthProxy.v; }
            })
            // Ring 1 淡出 + Ring 2 扩散（同步进行）
            .to(strengthProxy, {
                v: 0, duration: 0.8, ease: 'power2.out',
                onUpdate: function () {
                    ringStrength = strengthProxy.v;
                    ring2Scale = (1 - strengthProxy.v) * 0.56;
                    ring2Opacity = 1 - strengthProxy.v;
                }
            })
            // Ring 2 急收（与上一段重叠 0.5s）
            .to(r2Proxy, {
                v: 0, duration: 0.7, ease: 'power3.in',
                onUpdate: function () {
                    ring2Scale = r2Proxy.v;
                    ring2Opacity = r2Proxy.v;
                }
            }, '-=0.5')
            // Ring 3 缓缓展开（从 2.6s 起，与 Ring2 收回重叠）
            .to(r3Proxy, {
                v: 1, duration: 1.3, ease: 'power2.out',
                onUpdate: function () {
                    ring3Scale = r3Proxy.v * 0.56 * 0.85;
                    ring3Opacity = r3Proxy.v;
                }
            }, '2.6')
            // Ring 3 急收（重叠 0.5s）
            .to(r3Proxy, {
                v: 0, duration: 0.7, ease: 'power3.in',
                onUpdate: function () {
                    ring3Scale = r3Proxy.v;
                    ring3Opacity = r3Proxy.v;
                }
            }, '-=0.5');
        // 时间轴实际总长 = 最晚结束的 tween = 4.1s（Ring3 急收完成），repeat 无缝循环
        // 粒子呼吸循环 4.6s、点阵波纹周期 4.2s —— 三者轻微失谐，
        // 每轮图案略有不同，避免机械重复感（与参考网站的参数一致）

        // ---- 粒子呼吸时间线（同 4.6s 循环）----
        var pProxy = { v: 0 };
        gsap.timeline({ repeat: -1, timeScale: SPEED })
            .to(pProxy, {
                v: 1, duration: 1.0, ease: 'power2.out',
                onUpdate: function () { particleStrength = pProxy.v; }
            })
            .to(pProxy, {
                v: 1, duration: 0.8, ease: 'none',
                onUpdate: function () { particleStrength = pProxy.v; }
            })
            .to(pProxy, {
                v: 0, duration: 2.8, ease: 'power2.out',
                onUpdate: function () { particleStrength = pProxy.v; }
            });

        return function () {
            /* 呼吸值已由时间线 onUpdate 持续写入 */
        };
    }

    // ============ 主循环 + 性能控制 ============

    function boot() {
        var wrapper = document.getElementById('hero-fluid');
        var ring = wrapper ? createWaveRing(wrapper) : null;
        var particles = createParticles(dotCanvas);
        var updateFallback = startTimeline();

        // hero 滚出屏幕 → 暂停渲染省电
        var visible = true;
        var hero = document.querySelector('.hero');
        if (hero && 'IntersectionObserver' in window) {
            new IntersectionObserver(function (entries) {
                visible = entries[0].isIntersecting;
            }, { threshold: 0 }).observe(hero);
        }

        function frame() {
            requestAnimationFrame(frame);
            if (!visible) return;

            updateFallback();
            if (ring) ring.tick();
            if (particles) particles.draw();
        }
        requestAnimationFrame(frame);
    }

    boot();
})();
