"""Interactive retail voice agent using the official LiveKit session runtime."""
import hashlib
import logging

from livekit.agents import APIConnectOptions, Agent, AgentServer, AgentSession, JobContext, TurnHandlingOptions, cli
from livekit.agents.voice.agent_session import SessionConnectOptions
from livekit.plugins import deepgram, openai, silero

from config import Settings, TAU_COMMIT, LLM_BASE_URL
from benchmark import RetailBenchmark
from tracing import RunTrace

logger = logging.getLogger("voice-eval-lab")
server = AgentServer()


def build_agent(settings: Settings, trace: RunTrace):
    benchmark = RetailBenchmark(settings.task_id, trace.emit)
    prompt = settings.prompt_path.read_text()
    instructions = prompt + "\n\n" + benchmark.policy
    agent = Agent(instructions=instructions, tools=benchmark.tools())
    session = AgentSession(
        stt=deepgram.STT(model=settings.stt_model, language="en-US"),
        llm=openai.LLM(model=settings.llm_model, base_url=LLM_BASE_URL,
                       api_key=settings.llm_api_key, temperature=0, parallel_tool_calls=False,
                       reasoning_effort="low"),
        tts=deepgram.TTS(model=settings.tts_model),
        vad=silero.VAD.load(),
        turn_handling=TurnHandlingOptions(
            turn_detection="vad", endpointing={"min_delay": 1.2, "max_delay": 3.0},
            preemptive_generation={"enabled": False},
        ),
        # Keep retries in the SDK rather than introducing a custom retry loop.
        conn_options=SessionConnectOptions(
            llm_conn_options=APIConnectOptions(max_retry=2, retry_interval=2, timeout=60),
        ),
        max_tool_steps=12,
        transcription_timeout=5,
    )
    trace.attach(session)
    trace.save("config.json", {
        "task_id": settings.task_id, "domain": "retail", "mode": "interactive",
        "llm": settings.llm_model, "stt": settings.stt_model, "tts": settings.tts_model,
        "llm_provider": "command-code", "llm_base_url": LLM_BASE_URL,
        "temperature": 0, "parallel_tool_calls": False, "max_tool_steps": 12,
        "reasoning_effort": "low",
        "turn_detection": "vad", "tau_commit": TAU_COMMIT,
        "endpointing_min_delay": 1.2, "endpointing_max_delay": 3.0,
        "preemptive_generation": False,
        "llm_retry_interval": 2, "llm_max_retry": 2,
        "instructions_sha256": hashlib.sha256(instructions.encode()).hexdigest(),
    })
    (trace.directory / "instructions.txt").write_text(instructions)
    # Customer-only information is saved for the human operator, never added to agent context.
    trace.save("customer_scenario.json", benchmark.task.user_scenario.model_dump(mode="json"))
    trace.save("initial_state.json", benchmark.snapshot())
    return session, agent, benchmark


async def save_report(ctx: JobContext):
    trace = ctx.proc.userdata.pop("trace", None)
    if trace:
        trace.save("session_report.json", ctx.make_session_report().to_dict())


@server.rtc_session(on_session_end=save_report)
async def entrypoint(ctx: JobContext):
    settings = Settings.load()
    trace = RunTrace(settings.task_id)
    session, agent, benchmark = build_agent(settings, trace)
    ctx.proc.userdata["trace"] = trace
    logger.info("Run evidence: %s", trace.directory)

    async def shutdown():
        await session.aclose()
        for provider in (session.stt, session.llm, session.tts):
            await provider.aclose()
        trace.finish(session, benchmark)

    ctx.add_shutdown_callback(shutdown)
    await session.start(agent=agent, room=ctx.room, record=False)
    await ctx.connect()
    # Let the customer open the conversation, as in the benchmark.


if __name__ == "__main__":
    cli.run_app(server)
