import asyncio
import logging

from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.agent.job_agent import JobAgent
from app.services.upload_service import (
    extract_text_from_file,
    validate_file_extension,
    validate_file_size,
    DEFAULT_MAX_SIZE,
)

router = APIRouter()
job_agent = JobAgent()
_logger = logging.getLogger(__name__)


class ResumeInput(BaseModel):
    resume_text: str


class JDInput(BaseModel):
    jd_text: str


class MatchInput(BaseModel):
    resume_json: str
    jd_json: str


class OptimizeInput(BaseModel):
    resume_text: str
    jd_text: str
    match_result: str


class PlanInput(BaseModel):
    resume_summary: str
    jd_text: str
    match_result: str


class FullPipelineInput(BaseModel):
    resume_text: str
    jd_text: str


class InterviewInput(BaseModel):
    company: str
    position: str
    interview_type: Optional[str] = "综合面试"


class SalaryInput(BaseModel):
    city: str
    industry: str
    position: str
    experience: Optional[str] = ""
    expected_salary: Optional[str] = "面议"


class GuideInput(BaseModel):
    scenario: str
    goal: Optional[str] = "成功求职"


class FeedbackInput(BaseModel):
    rating: int
    comment: Optional[str] = ""
    related_query: Optional[str] = ""
    related_answer: Optional[str] = ""


@router.post("/resume", summary="解析简历")
async def parse_resume(
    request: ResumeInput,
    current_user: User = DependAuth,
):
    try:
        result = await job_agent.analyze_resume(request.resume_text)
        return Success(data=result)
    except Exception:
        _logger.exception("简历解析失败")
        return Fail(code=500, msg="简历解析失败，请稍后重试")


@router.post("/jd", summary="分析岗位描述")
async def parse_jd(
    request: JDInput,
    current_user: User = DependAuth,
):
    try:
        result = await job_agent.analyze_jd(request.jd_text)
        return Success(data=result)
    except Exception:
        _logger.exception("JD 分析失败")
        return Fail(code=500, msg="JD 分析失败，请稍后重试")


@router.post("/match", summary="匹配度分析")
async def calculate_match(
    request: MatchInput,
    current_user: User = DependAuth,
):
    try:
        result = await job_agent.calculate_match(request.resume_json, request.jd_json)
        return Success(data=result)
    except Exception:
        _logger.exception("匹配分析失败")
        return Fail(code=500, msg="匹配分析失败，请稍后重试")


@router.post("/optimize", summary="简历优化")
async def optimize_resume(
    request: OptimizeInput,
    current_user: User = DependAuth,
):
    try:
        result = await job_agent.optimize_resume(
            request.resume_text, request.jd_text, request.match_result
        )
        return Success(data={"optimized_resume": result})
    except Exception:
        _logger.exception("简历优化失败")
        return Fail(code=500, msg="简历优化失败，请稍后重试")


@router.post("/optimize-rag", summary="RAG增强简历优化（含文档溯源+匹配度报告）")
async def optimize_resume_rag(
    request: OptimizeInput,
    current_user: User = DependAuth,
):
    try:
        result = await job_agent.optimize_resume_with_rag(
            request.resume_text, request.jd_text, request.match_result
        )
        return Success(data=result)
    except Exception:
        _logger.exception("RAG简历优化失败")
        return Fail(code=500, msg="RAG简历优化失败，请稍后重试")


@router.post("/plan", summary="生成投递计划")
async def generate_plan(
    request: PlanInput,
    current_user: User = DependAuth,
):
    try:
        result = await job_agent.generate_plan(
            request.resume_summary, request.jd_text, request.match_result
        )
        return Success(data={"plan": result})
    except Exception:
        _logger.exception("计划生成失败")
        return Fail(code=500, msg="计划生成失败，请稍后重试")


@router.post("/interview", summary="面试问答生成（RAG增强）")
async def generate_interview(
    request: InterviewInput,
    current_user: User = DependAuth,
):
    try:
        result = await job_agent.generate_interview(
            request.company, request.position, request.interview_type
        )
        return Success(data={"interview": result})
    except Exception:
        _logger.exception("面试问答生成失败")
        return Fail(code=500, msg="面试问答生成失败，请稍后重试")


@router.post("/salary", summary="薪资谈判建议（RAG增强）")
async def generate_salary_advice(
    request: SalaryInput,
    current_user: User = DependAuth,
):
    try:
        result = await job_agent.generate_salary_advice(
            request.city, request.industry, request.position,
            request.experience, request.expected_salary,
        )
        return Success(data={"salary_advice": result})
    except Exception:
        _logger.exception("薪资建议生成失败")
        return Fail(code=500, msg="薪资建议生成失败，请稍后重试")


@router.post("/guide", summary="求职攻略生成（RAG增强）")
async def generate_guide(
    request: GuideInput,
    current_user: User = DependAuth,
):
    try:
        result = await job_agent.generate_guide(request.scenario, request.goal)
        return Success(data={"guide": result})
    except Exception:
        _logger.exception("攻略生成失败")
        return Fail(code=500, msg="攻略生成失败，请稍后重试")


@router.post("/feedback", summary="提交用户反馈")
async def submit_feedback(
    request: FeedbackInput,
    current_user: User = DependAuth,
):
    try:
        from app.tools.feedback_tool import FeedbackTool
        feedback_tool = FeedbackTool()
        result = await feedback_tool.run(
            rating=str(request.rating),
            comment=request.comment,
            related_query=request.related_query,
            related_answer=request.related_answer,
            user_id=current_user.username,
        )
        return Success(data={"message": result})
    except Exception:
        _logger.exception("反馈提交失败")
        return Fail(code=500, msg="反馈提交失败，请稍后重试")


@router.post("/pipeline", summary="完整求职流程（RAG增强）")
async def full_pipeline(
    request: FullPipelineInput,
    current_user: User = DependAuth,
):
    try:
        result = await asyncio.wait_for(
            job_agent.full_pipeline(request.resume_text, request.jd_text),
            timeout=180,
        )
        return Success(data=result)
    except asyncio.TimeoutError:
        _logger.error("求职流程整体超时")
        return Fail(code=504, msg="求职分析超时，请简化输入后重试")
    except TimeoutError:
        _logger.error("LLM 调用超时")
        return Fail(code=504, msg="AI 服务响应超时，请稍后重试")
    except Exception:
        _logger.exception("求职流程执行失败")
        return Fail(code=500, msg="求职流程执行失败，请稍后重试")


@router.post("/parse-file", summary="解析文件提取文本（临时使用，不入库）")
async def parse_file(
    file: UploadFile = File(...),
    current_user: User = DependAuth,
):
    if not file.filename:
        return Fail(code=400, msg="文件名不能为空")

    err = validate_file_extension(file.filename)
    if err:
        return err

    try:
        content = await file.read()

        err = validate_file_size(len(content), DEFAULT_MAX_SIZE)
        if err:
            return err

        documents = extract_text_from_file(file.filename, content)

        if not documents:
            return Fail(code=400, msg="无法从文件中提取文本内容")

        full_text = "\n\n".join(documents)
        return Success(data={
            "text": full_text,
            "filename": file.filename,
            "pages": len(documents),
        })
    except Exception:
        _logger.exception("文件解析失败")
        return Fail(code=500, msg="文件解析失败，请稍后重试")
