"""FastAPI 应用 - 头脑风暴智能体 API 接口"""
import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from pathlib import Path
from app.roles.white_hat import WhiteHat
from app.roles.red_hat import RedHat
from app.roles.black_hat import BlackHat
from app.roles.yellow_hat import YellowHat
from app.roles.green_hat import GreenHat
from app.roles.purple_hat import PurpleHat
from app.orchestrator.supervisor import Supervisor
from app.orchestrator.debater import DebateEngine
from app.orchestrator.summarizer import Summarizer
from app.config import settings

# 初始化 6 个角色
ROLES = [
    WhiteHat(),
    RedHat(),
    BlackHat(),
    YellowHat(),
    GreenHat(),
    PurpleHat()
]

# 初始化协调者和引擎
supervisor = Supervisor()
debater = DebateEngine(ROLES)
summarizer = Summarizer()

app = FastAPI(
    title="头脑风暴智能体 API",
    description="基于六顶思考帽的 Multi-Agent 辩证推理系统",
    version="1.0.0"
)

# 配置 CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BrainstormRequest(BaseModel):
    """头脑风暴请求"""
    question: str
    max_rounds: int = 2


class BrainstormResponse(BaseModel):
    """头脑风暴响应"""
    problem_type: str
    selected_roles: list[str]
    debate_results: dict
    final_report: str


class SSEEvent(BaseModel):
    """SSE 事件"""
    event: str
    data: dict


@app.post("/brainstorm", response_model=BrainstormResponse)
async def brainstorm(req: BrainstormRequest):
    """
    头脑风暴接口（同步版本）
    
    Args:
        req: 包含用户问题的请求对象
        
    Returns:
        完整的辩论结果和综合报告
    """
    # Step 1: 协调者分类问题
    classification = supervisor.classify_problem(req.question)
    
    # Step 2: 执行辩论
    debate_results = debater.execute_debate(req.question)
    
    # Step 3: 生成综合报告
    final_report = summarizer.generate_report(debate_results)
    
    return BrainstormResponse(
        problem_type=classification["problem_type"],
        selected_roles=classification["selected_roles"],
        debate_results=debate_results,
        final_report=final_report
    )


@app.post("/brainstorm/stream")
async def brainstorm_stream(req: BrainstormRequest):
    """
    头脑风暴接口（流式版本 - SSE）
    
    实时返回每个阶段的进度，避免长时间等待
    
    Args:
        req: 包含用户问题的请求对象
        
    Yields:
        SSE 事件流
    """
    async def event_generator():
        try:
            # Step 1: 分类问题
            yield f"event: status\ndata: {json.dumps({'status': 'classifying', 'message': '协调者分析问题类型...'})}\n\n"
            await asyncio.sleep(0.1)
            
            classification = supervisor.classify_problem(req.question)
            yield f"event: classification\ndata: {json.dumps(classification)}\n\n"
            
            # Step 2: 执行辩论 - Round 1
            yield f"event: status\ndata: {json.dumps({'status': 'debating', 'round': 1, 'message': 'Round 1: 独立思考...'})}\n\n"
            await asyncio.sleep(0.1)
            
            debate_results = {"round_1": {}, "round_2": {}}
            
            # 并行执行 Round 1
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            with ThreadPoolExecutor(max_workers=len(ROLES)) as executor:
                futures = {}
                for role in ROLES:
                    future = executor.submit(role.think, req.question, context=None, use_strong_model=False)
                    futures[future] = role
                
                for future in as_completed(futures):
                    role = futures[future]
                    try:
                        view = future.result()
                        debate_results["round_1"][role.color] = view
                        yield f"event: progress\ndata: {json.dumps({'status': 'role_complete', 'round': 1, 'role': role.color, 'role_name': role.name})}\n\n"
                    except Exception as e:
                        debate_results["round_1"][role.color] = f"执行失败: {str(e)}"
            
            yield f"event: round_complete\ndata: {json.dumps({'round': 1, 'results': debate_results['round_1']})}\n\n"
            
            # Step 3: 执行辩论 - Round 2
            if req.max_rounds >= 2:
                yield f"event: status\ndata: {json.dumps({'status': 'debating', 'round': 2, 'message': 'Round 2: 交叉辩驳...'})}\n\n"
                await asyncio.sleep(0.1)
                
                with ThreadPoolExecutor(max_workers=len(ROLES)) as executor:
                    futures = {}
                    for role in ROLES:
                        future = executor.submit(role.think, req.question, context=debate_results["round_1"], use_strong_model=False)
                        futures[future] = role
                    
                    for future in as_completed(futures):
                        role = futures[future]
                        try:
                            rebuttal = future.result()
                            debate_results["round_2"][role.color] = rebuttal
                            yield f"event: progress\ndata: {json.dumps({'status': 'role_complete', 'round': 2, 'role': role.color, 'role_name': role.name})}\n\n"
                        except Exception as e:
                            debate_results["round_2"][role.color] = f"执行失败: {str(e)}"
                
                yield f"event: round_complete\ndata: {json.dumps({'round': 2, 'results': debate_results['round_2']})}\n\n"
            
            # Step 4: 生成报告
            yield f"event: status\ndata: {json.dumps({'status': 'summarizing', 'message': '生成综合报告...'})}\n\n"
            await asyncio.sleep(0.1)
            
            final_report = summarizer.generate_report(debate_results)
            
            # Step 5: 返回最终结果
            yield f"event: complete\ndata: {json.dumps({
                'problem_type': classification['problem_type'],
                'selected_roles': classification['selected_roles'],
                'debate_results': debate_results,
                'final_report': final_report
            })}\n\n"
            
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/health")
def health():
    """健康检查接口"""
    return {"status": "ok", "version": "1.0.0"}


@app.get("/roles")
def list_available_roles():
    """列出所有可用角色"""
    return {
        "roles": [
            {
                "name": role.name,
                "color": role.color,
                "description": role.system_prompt[:100] + "..."
            }
            for role in ROLES
        ]
    }


# 挂载静态文件服务（Web 界面）
web_dir = Path(__file__).parent.parent.parent / "web"
if web_dir.exists():
    app.mount("/web", StaticFiles(directory=str(web_dir), html=True), name="web")
    
    # 根路径重定向到 Web 界面
    @app.get("/")
    def root():
        """根路径 - 返回 Web 界面"""
        index_file = web_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "头脑风暴智能体 API 已启动，访问 /docs 查看 API 文档"}
