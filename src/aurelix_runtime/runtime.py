        self.handlers[kind] = handler

    def register_pipeline(self, pipeline: GovernedPipeline | None = None, kind: str = "pipeline.run") -> None:
        governed = pipeline or GovernedPipeline()

        def handle(payload: dict[str, str]) -> None:
            objective = payload.get("objective", "").strip()
            if not objective:
                raise ValueError("pipeline objective is required")
            governed.run(objective, business_approved=False)

        self.register(kind, handle)

    def register_experiment(self, experiment: Experiment) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.store.lock, self.store.db:
            self.store.db.execute(
                """INSERT INTO experiments(experiment_id,hypothesis,success_criteria,status,result,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(experiment_id) DO UPDATE SET hypothesis=excluded.hypothesis,
                   success_criteria=excluded.success_criteria, status=excluded.status,
                   result=excluded.result, updated_at=excluded.updated_at""",
                (experiment.id, experiment.hypothesis, json.dumps(experiment.success_criteria), experiment.status,
                 json.dumps(experiment.result) if experiment.result is not None else None, now, now),
            )

    def record_observation(self, experiment_id: str, observation: dict[str, Any]) -> str:
        observation_id = str(uuid4())
        with self.store.lock, self.store.db:
            self.store.db.execute(
                "INSERT INTO observations(id,experiment_id,observation,recorded_at) VALUES (?,?,?,?)",
                (observation_id, experiment_id, json.dumps(observation), datetime.now(timezone.utc).isoformat()),
            )
        return observation_id

    def query_experiment_observations(self, experiment_id: str) -> list[dict[str, Any]]:
        with self.store.lock:
            rows = self.store.db.execute(
                "SELECT observation FROM observations WHERE experiment_id=? ORDER BY recorded_at",
                (experiment_id,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    def query_experiments(self, status: str | None = None) -> list[dict[str, Any]]:
        with self.store.lock:
            if status:
                rows = self.store.db.execute(
                    "SELECT experiment_id,hypothesis,success_criteria,status,result,created_at,updated_at FROM experiments WHERE status=? ORDER BY created_at DESC",
                    (status,),
                ).fetchall()
            else:
                rows = self.store.db.execute(
                    "SELECT experiment_id,hypothesis,success_criteria,status,result,created_at,updated_at FROM experiments ORDER BY created_at DESC"
                ).fetchall()
        return [
            {
                "experiment_id": row[0], "hypothesis": row[1], "success_criteria": json.loads(row[2]),
                "status": row[3], "result": json.loads(row[4]) if row[4] else None,
                "created_at": row[5], "updated_at": row[6],
            }
            for row in rows
        ]

    def get_experiment(self, experiment_id: str) -> Experiment:
        match = next((item for item in self.query_experiments() if item["experiment_id"] == experiment_id), None)
        if match is None:
            raise KeyError(f"experiment not found: {experiment_id}")
        return Experiment(
            id=match["experiment_id"],
            hypothesis=match["hypothesis"],
            success_criteria=match["success_criteria"],
            status=match["status"],
            result=match["result"],
        )

    def create_experiment_runner(self) -> ExperimentRunner:
        def collector(experiment: Experiment) -> list[dict[str, Any]]:
            self.register_experiment(experiment)
            return self.query_experiment_observations(experiment.id)

        def on_complete(experiment: Experiment, _run) -> None:
            self.register_experiment(experiment)
            self.store.audit(
                "experiment.evaluated",
                "experiment-runner",
                experiment.id,
                "succeeded" if experiment.result and experiment.result.get("passed") else "evaluated",
                experiment.result or {},
            )

        return ExperimentRunner(collector=collector, evaluator=EvaluationEngine(), on_complete=on_complete)
