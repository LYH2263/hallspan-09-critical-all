# HallSpan 考场间距排座

在考室网格上按最小曼哈顿距离排座，同试卷套不得四邻相邻，并输出违规与统计。

技术栈：Python 3.12 / FastAPI / SQLAlchemy / PostgreSQL / Vue 3 / TypeScript / Vite

## 场次封闭与开放

场次状态是会话级开关，不是单条排座规则，二者互斥，由提交排座瞬间的名册决定：

- **封闭场**：名册中至少有一名「关键考生」。必须全员落座，未排统计恒为 0、未排入口关闭；
  做不到则整场失败（`409 封闭场必须全员落座`），不新增方案。
- **开放场**：名册中没有任何关键标记。允许现网未排（局部未排照常出方案）。

在「考生名册」页用 `PATCH /api/candidates/{id}`（`{"is_key": true|false}`）增删关键标记；
改动在下一次提交排座瞬间生效，旧状态的方案图不会被继续沿用。

种子数据：5×6 考室、最小间距 2（最多坐 15 人）、16 名考生且首名为关键 —— 格位紧张，
封闭场必然失败不增方案；取消全部关键标记后转入开放场，允许 1 人未排。

## 启动

```bash
docker compose up --build
```

| 服务 | 地址 |
| --- | --- |
| 前端 | http://localhost:4900 |
| API | http://localhost:9900 |
| API 文档 | http://localhost:9900/docs |
| Postgres | localhost:5450 |

健康检查：`GET http://localhost:9900/api/health`

## 使用说明

1. 在「考室」「考生」「试卷套」确认基础数据。
2. 打开「排座图」执行间距排座。
3. 在「违规」查看间距或同卷相邻问题。
4. 在「统计」查看占用与违规汇总。

## 开发与测试

```bash
docker compose exec api pytest -q
```
