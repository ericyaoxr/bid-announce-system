# MEMORY.md - 长期记忆

## 项目: 中标结果公示系统

### 核心架构
- **爬虫**: `src/crawlers/deep_crawler.py` - 5种公告类型 + 详情页深度抓取
- **API**: `src/api/app_v2.py` - FastAPI, 连接 `data/announcements_deep.db`
- **前端**: `web/index.html` - 纯HTML零CDN依赖, 含中标人/金额展示
- **启动**: `scripts/start_server.py` (Web服务), `scripts/run_deep_crawler.py` (爬虫)

### API端点
- 列表: `https://zcpt.szcg.cn/group-tendering-website/officialwebsite/project/page`
- 详情(结果/候选人): `https://zcpt.szcg.cn/group-tendering-website/officialwebsite/project/resultInfoDetail/{projectId}`
- 详情(变更): `https://zcpt.szcg.cn/group-tendering-website/officialwebsite/project/announcementChangeDetail/{projectId}`
- 参数: `announcementType`(1-5), `current`(页码), `size`(每页数)

### 导出功能
- CSV: `GET /api/export/csv` (UTF-8 BOM, Excel兼容)
- Excel: `GET /api/export/excel` (openpyxl, 含样式/筛选/冻结)
- 17列: 公告ID/项目编号/标题/分类/方式/招标人/联系人/联系电话/发布时间/项目地址/资金来源/控制价/中标金额/中标人/中标人金额/信用代码/详情链接
- 支持筛选条件(keyword/category/tender_mode)
- 中文文件名需 `urllib.parse.quote` 编码

### 关键决策
- 前端不用CDN（网络问题），纯HTML+CSS+JS实现
- 深度数据库独立: `announcements_deep.db`（含30+字段）
- 中标人数据从 `resultInfoDetail` API的 `projectPublicityRecordVO.winningBidders` 提取
- 服务器绑定 `0.0.0.0`（IDE内置浏览器兼容）
- **列表按中标人展开**：只展开is_winning=1的中标人，非中标候选人不展开
- Dashboard统计也用展开后的数字
- 导出也按中标人展开（每个中标人一行，仅is_winning=1）
- 多中标人时显示 `[1/3]` 序号标识
- Dashboard: 中标数最多公司TOP10 + 中标总金额最高公司TOP10（取代单个公司卡片）
- 列表支持每页10/20/50/100条切换
- 列表去掉截止时间列，详情弹窗也去掉

### 用户偏好
- Ericyao, Windows系统, 中山居住深圳工作
- 对交易极度谨慎，要求白纸黑字合同
- 关注中标人和中标金额，要求深度数据
