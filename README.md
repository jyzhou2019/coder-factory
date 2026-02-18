# Coder-Factory

> AI 自主代码工厂 - 从需求到交付的全自动化生产线

## 核心能力

- **需求解析**: 将自然语言需求分解为可执行任务
- **交互确认**: 多轮对话澄清和确认用户意图
- **架构设计**: 智能匹配技术栈，生成系统架构
- **代码生成**: AI 驱动的多语言代码生成
- **自动测试**: 生成并执行完整测试套件
- **容器交付**: Docker 化的一键部署

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/jyzhou2019/coder-factory.git
cd coder-factory

# 使用 Docker Compose 启动
docker-compose up -d

# 或使用 Docker 直接构建
docker build -t coder-factory .
docker run -it coder-factory
```

## 架构

```
用户需求 → 需求解析 → 交互确认 → 架构设计 → 代码生成 → 测试验证 → 容器部署 → 产品交付
```

## 项目状态

🚧 开发中 - 当前版本: 0.1.0

## License

MIT
