from aurelix_runtime.engineering_loop import EngineeringLoop, LoopContext, Stage


def test_full_loop_can_execute_through_opportunity() -> None:
    loop = EngineeringLoop()
    for stage in loop.ORDER[:-1]:
        loop.register(stage, lambda ctx, stage=stage: LoopContext(ctx.objective, {**ctx.data, stage.value: True}, list(ctx.history)))
    result = loop.run(LoopContext("find a first revenue opportunity"))
    assert result.history == list(loop.ORDER[:-1])
    assert Stage.BUSINESS not in result.history


def test_missing_stage_is_detected() -> None:
    loop = EngineeringLoop()
    loop.register(Stage.GOVERNOR, lambda ctx: ctx)
    assert Stage.RESEARCH in loop.missing_stages()
