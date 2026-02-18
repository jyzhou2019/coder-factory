"""
技术栈知识库 (F003)

维护常用技术栈的信息和推荐规则
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProjectCategory(Enum):
    """项目类型分类"""
    WEB_APP = "web_app"              # Web 应用
    API_SERVICE = "api_service"      # API 服务
    CLI_TOOL = "cli_tool"            # 命令行工具
    DESKTOP_APP = "desktop_app"      # 桌面应用
    MOBILE_APP = "mobile_app"        # 移动应用
    LIBRARY = "library"              # 库/包
    DATA_PIPELINE = "data_pipeline"  # 数据管道
    MICROSERVICE = "microservice"    # 微服务
    STATIC_SITE = "static_site"      # 静态网站
    REALTIME_APP = "realtime_app"    # 实时应用


class ScaleLevel(Enum):
    """规模级别"""
    SMALL = "small"      # 小型项目 (< 1000 行)
    MEDIUM = "medium"    # 中型项目 (1000-10000 行)
    LARGE = "large"      # 大型项目 (> 10000 行)


@dataclass
class TechOption:
    """技术选项"""
    name: str
    category: str          # runtime/framework/database/etc
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    best_for: list[str] = field(default_factory=list)
    complexity: int = 1    # 1-5 学习和使用复杂度
    popularity: int = 3    # 1-5 流行度
    performance: int = 3   # 1-5 性能评分


@dataclass
class TechStackTemplate:
    """技术栈模板"""
    name: str
    category: ProjectCategory
    runtime: str
    frontend: Optional[str] = None
    backend: Optional[str] = None
    database: Optional[str] = None
    additional: list[str] = field(default_factory=list)
    description: str = ""
    use_cases: list[str] = field(default_factory=list)


# 技术选项知识库
TECH_OPTIONS: dict[str, TechOption] = {
    # 运行时
    "python": TechOption(
        name="Python",
        category="runtime",
        pros=["语法简洁", "生态丰富", "开发效率高", "AI/ML 友好"],
        cons=["性能相对较低", "GIL 限制"],
        best_for=["Web 后端", "数据科学", "AI/ML", "自动化脚本"],
        complexity=1,
        popularity=5,
        performance=3,
    ),
    "nodejs": TechOption(
        name="Node.js",
        category="runtime",
        pros=["异步IO高效", "前后端统一语言", "npm 生态丰富"],
        cons=["回调地狱", "CPU 密集型任务性能差"],
        best_for=["实时应用", "API 服务", "单页应用"],
        complexity=2,
        popularity=5,
        performance=4,
    ),
    "go": TechOption(
        name="Go",
        category="runtime",
        pros=["高性能", "并发原生支持", "部署简单", "编译快"],
        cons=["错误处理繁琐", "泛型支持有限"],
        best_for=["微服务", "高并发服务", "CLI 工具"],
        complexity=2,
        popularity=4,
        performance=5,
    ),
    "rust": TechOption(
        name="Rust",
        category="runtime",
        pros=["内存安全", "零成本抽象", "极高性能"],
        cons=["学习曲线陡峭", "编译慢"],
        best_for=["系统编程", "WebAssembly", "高性能服务"],
        complexity=5,
        popularity=3,
        performance=5,
    ),

    # 前端框架
    "react": TechOption(
        name="React",
        category="frontend",
        pros=["组件化", "生态成熟", "灵活"],
        cons=["需要额外学习状态管理", "配置繁琐"],
        best_for=["单页应用", "大型前端项目"],
        complexity=3,
        popularity=5,
        performance=4,
    ),
    "vue": TechOption(
        name="Vue",
        category="frontend",
        pros=["易上手", "文档友好", "渐进式"],
        cons=["生态相对较小", "TypeScript 支持不如 React"],
        best_for=["中小型项目", "快速原型"],
        complexity=2,
        popularity=4,
        performance=4,
    ),
    "svelte": TechOption(
        name="Svelte",
        category="frontend",
        pros=["编译时优化", "无虚拟DOM", "包体积小"],
        cons=["生态较小", "社区资源少"],
        best_for=["轻量级应用", "性能敏感项目"],
        complexity=2,
        popularity=3,
        performance=5,
    ),

    # 后端框架
    "fastapi": TechOption(
        name="FastAPI",
        category="backend",
        pros=["自动文档", "类型提示", "异步支持", "高性能"],
        cons=["相对较新", "部分功能需要额外配置"],
        best_for=["API 服务", "微服务"],
        complexity=2,
        popularity=4,
        performance=5,
    ),
    "django": TechOption(
        name="Django",
        category="backend",
        pros=["功能全面", "Admin 后台", "ORM 强大", "安全"],
        cons=["重量级", "灵活性较低"],
        best_for=["内容管理", "企业应用", "快速开发"],
        complexity=2,
        popularity=4,
        performance=3,
    ),
    "express": TechOption(
        name="Express",
        category="backend",
        pros=["轻量级", "灵活", "中间件丰富"],
        cons=["缺乏约定", "需要手动配置很多功能"],
        best_for=["API 服务", "小型项目"],
        complexity=2,
        popularity=5,
        performance=4,
    ),
    "nestjs": TechOption(
        name="NestJS",
        category="backend",
        pros=["结构化", "TypeScript 原生", "依赖注入"],
        cons=["学习曲线", "配置复杂"],
        best_for=["企业级应用", "大型项目"],
        complexity=3,
        popularity=4,
        performance=4,
    ),

    # 数据库
    "postgresql": TechOption(
        name="PostgreSQL",
        category="database",
        pros=["功能强大", "ACID 兼容", "扩展性好"],
        cons=["配置复杂", "水平扩展难"],
        best_for=["关系型数据", "复杂查询", "企业应用"],
        complexity=3,
        popularity=4,
        performance=4,
    ),
    "mongodb": TechOption(
        name="MongoDB",
        category="database",
        pros=["灵活schema", "水平扩展", "JSON 原生"],
        cons=["无事务(早期)", "占用空间大"],
        best_for=["文档型数据", "快速迭代", "大数据"],
        complexity=2,
        popularity=4,
        performance=4,
    ),
    "sqlite": TechOption(
        name="SQLite",
        category="database",
        pros=["零配置", "单文件", "轻量"],
        cons=["并发写入限制", "不适合大规模"],
        best_for=["小型项目", "嵌入式", "开发测试"],
        complexity=1,
        popularity=4,
        performance=3,
    ),
    "redis": TechOption(
        name="Redis",
        category="database",
        pros=["极快", "数据结构丰富", "持久化支持"],
        cons=["内存限制", "单线程"],
        best_for=["缓存", "会话存储", "实时数据"],
        complexity=2,
        popularity=4,
        performance=5,
    ),
}


# 技术栈模板
TECH_STACK_TEMPLATES: list[TechStackTemplate] = [
    # Python 技术栈
    TechStackTemplate(
        name="Python FastAPI + React",
        category=ProjectCategory.WEB_APP,
        runtime="python",
        frontend="react",
        backend="fastapi",
        database="postgresql",
        additional=["sqlalchemy", "pydantic", "docker"],
        description="现代 Python 全栈，适合 API 密集型应用",
        use_cases=["SaaS 应用", "数据驱动型 Web"],
    ),
    TechStackTemplate(
        name="Python Django 全栈",
        category=ProjectCategory.WEB_APP,
        runtime="python",
        frontend=None,  # Django Templates
        backend="django",
        database="postgresql",
        additional=["django-rest-framework"],
        description="电池齐全的 Python Web 框架",
        use_cases=["内容管理", "企业内部系统"],
    ),
    TechStackTemplate(
        name="Python FastAPI 微服务",
        category=ProjectCategory.MICROSERVICE,
        runtime="python",
        backend="fastapi",
        database="postgresql",
        additional=["redis", "docker", "kubernetes"],
        description="轻量级微服务架构",
        use_cases=["微服务后端", "API 网关"],
    ),

    # Node.js 技术栈
    TechStackTemplate(
        name="Node.js Express + React",
        category=ProjectCategory.WEB_APP,
        runtime="nodejs",
        frontend="react",
        backend="express",
        database="mongodb",
        additional=["mongoose", "jsonwebtoken"],
        description="经典 MERN 栈变体",
        use_cases=["全栈 JavaScript", "初创项目"],
    ),
    TechStackTemplate(
        name="Node.js NestJS",
        category=ProjectCategory.API_SERVICE,
        runtime="nodejs",
        backend="nestjs",
        database="postgresql",
        additional=["typeorm", "class-validator"],
        description="企业级 Node.js 框架",
        use_cases=["企业 API", "大型后端"],
    ),

    # Go 技术栈
    TechStackTemplate(
        name="Go Gin API",
        category=ProjectCategory.API_SERVICE,
        runtime="go",
        backend="gin",
        database="postgresql",
        additional=["gorm", "docker"],
        description="高性能 Go API 服务",
        use_cases=["高并发 API", "微服务"],
    ),

    # CLI 工具
    TechStackTemplate(
        name="Python CLI",
        category=ProjectCategory.CLI_TOOL,
        runtime="python",
        additional=["click", "rich"],
        description="Python 命令行工具",
        use_cases=["自动化脚本", "开发工具"],
    ),
    TechStackTemplate(
        name="Go CLI",
        category=ProjectCategory.CLI_TOOL,
        runtime="go",
        additional=["cobra", "viper"],
        description="高性能 Go 命令行工具",
        use_cases=["系统工具", "DevOps 工具"],
    ),

    # 静态网站
    TechStackTemplate(
        name="静态站点生成",
        category=ProjectCategory.STATIC_SITE,
        runtime="nodejs",
        frontend=None,  # Next.js/Nuxt.js SSG
        additional=["nextjs", "tailwindcss"],
        description="静态站点生成",
        use_cases=["博客", "文档站", "营销页"],
    ),
]


class TechStackKnowledgeBase:
    """技术栈知识库"""

    def __init__(self):
        self.options = TECH_OPTIONS
        self.templates = TECH_STACK_TEMPLATES

    def get_option(self, name: str) -> Optional[TechOption]:
        """获取技术选项"""
        return self.options.get(name.lower())

    def get_templates_by_category(self, category: ProjectCategory) -> list[TechStackTemplate]:
        """按项目类型获取模板"""
        return [t for t in self.templates if t.category == category]

    def get_templates_by_runtime(self, runtime: str) -> list[TechStackTemplate]:
        """按运行时获取模板"""
        return [t for t in self.templates if t.runtime == runtime.lower()]

    def recommend_for_project(
        self,
        category: ProjectCategory,
        scale: ScaleLevel = ScaleLevel.MEDIUM,
        preferences: dict | None = None
    ) -> list[TechStackTemplate]:
        """
        为项目推荐技术栈

        Args:
            category: 项目类型
            scale: 项目规模
            preferences: 用户偏好 (runtime, database, etc.)

        Returns:
            list[TechStackTemplate]: 推荐的技术栈模板列表
        """
        templates = self.get_templates_by_category(category)

        if preferences:
            # 根据偏好过滤
            if "runtime" in preferences:
                templates = [t for t in templates if t.runtime == preferences["runtime"]]
            if "database" in preferences:
                templates = [t for t in templates if t.database == preferences["database"]]

        # 根据规模排序
        if scale == ScaleLevel.SMALL:
            # 小项目优先简单技术栈
            templates.sort(key=lambda t: len(t.additional))
        elif scale == ScaleLevel.LARGE:
            # 大项目优先成熟技术栈
            templates.sort(key=lambda t: -self._get_maturity_score(t))

        return templates

    def _get_maturity_score(self, template: TechStackTemplate) -> int:
        """获取技术栈成熟度评分"""
        score = 0
        if template.runtime:
            opt = self.options.get(template.runtime)
            if opt:
                score += opt.popularity
        if template.backend:
            opt = self.options.get(template.backend)
            if opt:
                score += opt.popularity
        if template.frontend:
            opt = self.options.get(template.frontend)
            if opt:
                score += opt.popularity
        return score

    def compare_techs(self, names: list[str]) -> dict:
        """比较多个技术选项"""
        result = {}
        for name in names:
            opt = self.get_option(name)
            if opt:
                result[name] = {
                    "complexity": opt.complexity,
                    "popularity": opt.popularity,
                    "performance": opt.performance,
                    "pros": opt.pros,
                    "cons": opt.cons,
                    "best_for": opt.best_for,
                }
        return result

    def get_all_runtimes(self) -> list[str]:
        """获取所有运行时"""
        return [name for name, opt in self.options.items() if opt.category == "runtime"]

    def get_all_frameworks(self, category: str = "backend") -> list[str]:
        """获取所有框架"""
        return [name for name, opt in self.options.items() if opt.category == category]

    def get_all_databases(self) -> list[str]:
        """获取所有数据库"""
        return [name for name, opt in self.options.items() if opt.category == "database"]
