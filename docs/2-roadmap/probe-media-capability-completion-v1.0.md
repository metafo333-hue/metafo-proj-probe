# probe / 元探 · 媒体能力补全 spec v1.0

> 日期：2026-06-14 · 性质：把"音乐/音频/媒体能力补全"按合规拆成可落地清单。
> 红线前提（不可破）：**不自建爬虫·不绕反爬/DRM·不下载平台版权音乐/视频**（已二次否决 2026-06-03/06-13）。
> 一句话：把"下载盗版"换成"授权获取 + 情报识别 + 自有处理"——同样让引擎完整，卖判断不卖盗版。

---

## 〇、合规分线（先分红绿，再谈实现）

| 动作 | 判定 |
|------|------|
| 从网易云/QQ音乐/抖音/Spotify/YouTube 下载受版权音乐/视频 | ❌ 红线（爬虫+绕DRM+版权侵权·法人担责）|
| 下载 CC/公共领域/授权曲库音乐（有官方 API）| ✅ 合规 |
| 处理用户自有/上传音频（ASR/分离/降噪）| ✅ 合规 |
| 授权 API 做听歌识曲 / 版权核查 / 元数据（供应商担责）| ✅ 合规 |

---

## 一、四方向补全清单（元东方四选全要）

### 方向1 · 音乐情报（识别 / 版权核查）— probe 卖判断的杀手锏

| 能力 | 实现 | 层 | key/成本 | 优先级 |
|------|------|----|---------|--------|
| 音乐元数据/发现 | **iTunes Search（已接）** + MusicBrainz（CC0·免费无key） | datasources/public | 免费无key | ✅ iTunes 已有·MusicBrainz P1 |
| 听歌识曲（音频→曲目） | ACRCloud / AudD 授权 API | extractors(remote)或datasource | **需 key·R8注册+R1付费** | P1·待授权 |
| **BGM 版权核查** | 识曲 → 比对授权/可商用状态 + 平台下架风险库 | services（情报合成） | 依赖识曲 | P2·护城河 |
| 歌词 | Musixmatch/Genius 授权 API | datasource | 需 key | P2 |
| 音乐榜单/趋势 | 公开榜单 API | datasources/public | 免费 | P2 |

> BGM 版权核查 = 创作者最痛点（日均下架20万条）。MVP = 识曲 + "这首在平台是否高下架风险"判断，非下载。

### 方向2 · 授权/免费音乐获取（真能下·仅授权曲库）

| 源 | 授权 | API | 优先级 |
|----|------|-----|--------|
| **Jamendo** | CC 授权·可商用 | 官方 API（需免费 client_id 注册·R8） | P1 |
| **Free Music Archive** | CC | API 现状须核实 ⚠️ | P2 |
| **Internet Archive (audio)** | 公共领域/CC | 官方 API·免费无key | P1（无key优先）|
| **ccMixter** | CC | API | P2 |

> 这些是"真下载"但**仅 CC/公共领域授权曲库**，供应商担责，合规。绝不混入平台版权曲。

### 方向3 · 自有音频处理增强（用户上传素材）

| 能力 | 库 | 许可 | 层 | 优先级 |
|------|----|----|----|--------|
| ASR 转写 | faster-whisper（**已建 audio.py**） | MIT | extractors(remote) | ✅ |
| 词级时间戳 | WhisperX | BSD-2 | extractors(remote) | P1 |
| 人声/伴奏分离 | Demucs（MIT·重ML·曾随旧栈移除·本身非爬虫·可重引） | MIT | extractors(remote·ufo GPU) | P2 |
| 降噪 | noisereduce / RNNoise | MIT/BSD | extractors(remote) | P3 |

### 方向4 · 其他媒体类型补全（引擎对"任意素材"完整）

| 类型 | 实现 | 层 | 优先级 |
|------|------|----|--------|
| **字幕文件 .srt/.vtt** | 纯解析（零依赖） | extractors | ✅ 本轮落 |
| 播客 | RSS enclosure → audio ASR（itunes_search 已发现层） | 组合现有 | P1 |
| 电子书 epub/mobi | Docling（已支持 epub） | extractors | ✅ 走 doc backend |
| 数据集/表格 csv/xlsx | Docling/markitdown（已支持） | extractors | ✅ 已覆盖 |
| 图像 OCR | RapidOCR（**已建 image.py**） | extractors(remote) | ✅ |

---

## 二、本轮落地（零key·零成本·可本地验证）

- **字幕提取器 `subtitle.py`**：.srt/.vtt → 纯文本，零依赖，autodiscover 自动入册（验证 D-Ext "加件不改架构" 再次成立）。
- classify 加 subtitle 路由（.srt/.vtt 后缀）。

## 三、待元东方决策（涉 key/R1/R8）

1. **ACRCloud / AudD 听歌识曲**：注册（R8 邮箱）+ 可能付费（R1）。识曲是音乐情报根基。要不要开？
2. **Jamendo client_id**：免费注册（R8），开授权音乐下载。
3. **歌词 API（Musixmatch/Genius）**：需 key。
4. **Demucs 重引**：MIT 合规，但重 ML（ufo GPU·P2000 5GB 实测）。要不要补人声分离？

## 四、与现有的关系

- 复用 D-Ext 自动发现：方向3/4 的提取器丢入 extractors/ 即注册。
- 重 ML（识曲/分离/ASR）走 D-Use 拓扑 → ufo 提取服务（server-roles 机6 禁 ML）。
- 音乐元数据/榜单走 datasources/public + orchestrator（已成熟·iTunes 为范例）。

## 关联
- 引擎深耕规划：[probe-engine-deepening-plan-v1.0.md](probe-engine-deepening-plan-v1.0.md)
- 合规红线真源：feasibility-v1 §5 · [[decision_probe_tikhub_keep_paid_20260613]]
- 现有音乐源：`app/datasources/public/itunes_search.py`
