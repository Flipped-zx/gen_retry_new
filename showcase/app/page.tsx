"use client";

import {
  ArrowRight,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleCheck,
  GitBranch,
  RotateCcw,
  ShieldCheck,
  Target,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import type { CSSProperties } from "react";
import {
  trajectories,
  type PromptDelta,
  type Trajectory,
  type TrajectoryDimension,
} from "./trajectory-data";

type FilterId = "all" | TrajectoryDimension;

const filters: { id: FilterId; label: string }[] = [
  { id: "all", label: "全部" },
  { id: "count", label: "计数与布局" },
  { id: "attribute", label: "属性绑定" },
  { id: "spatial", label: "空间关系" },
  { id: "action", label: "动作关系" },
  { id: "recovery", label: "历史恢复" },
];

const deltaIcon = {
  target: Target,
  preserve: ShieldCheck,
  forbid: X,
  branch: GitBranch,
};

function PromptParagraphs({ text }: { text: string }) {
  return (
    <div className="prompt-copy">
      {text.split("\n\n").map((paragraph) => {
        const separator = paragraph.indexOf(":");
        const hasLabel = separator > 0 && separator < 28;

        return (
          <p key={paragraph.slice(0, 48)}>
            {hasLabel ? (
              <>
                <strong>{paragraph.slice(0, separator + 1)}</strong>{" "}
                {paragraph.slice(separator + 1).trim()}
              </>
            ) : (
              paragraph
            )}
          </p>
        );
      })}
    </div>
  );
}

function DeltaChip({ delta }: { delta: PromptDelta }) {
  const Icon = deltaIcon[delta.kind];

  return (
    <span className={`delta-chip delta-${delta.kind}`}>
      <Icon size={14} strokeWidth={1.8} aria-hidden="true" />
      {delta.text}
    </span>
  );
}

function previewAttempts(trajectory: Trajectory) {
  if (trajectory.attempts.length <= 3) return trajectory.attempts;
  const middleIndex = Math.floor((trajectory.attempts.length - 1) / 2);
  return [
    trajectory.attempts[0],
    trajectory.attempts[middleIndex],
    trajectory.attempts[trajectory.attempts.length - 1],
  ];
}

function TrajectoryCard({
  trajectory,
  selected,
  onSelect,
}: {
  trajectory: Trajectory;
  selected: boolean;
  onSelect: () => void;
}) {
  const shownAttempts = previewAttempts(trajectory);
  const first = trajectory.attempts[0];
  const last = trajectory.attempts[trajectory.attempts.length - 1];
  const gain = last.passed - first.passed;

  return (
    <button
      className={`trajectory-card${selected ? " is-selected" : ""}`}
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
    >
      <span className="card-heading">
        <span>
          <small>{trajectory.index}</small>
          <strong>{trajectory.category}</strong>
        </span>
        <span className="card-gain">+{gain} ATOMS</span>
      </span>

      <span className="mini-attempts" aria-label={`${trajectory.title} 的代表性尝试`}>
        {shownAttempts.map((attempt, index) => (
          <span className="mini-attempt-step" key={attempt.id}>
            <span
              className={`mini-attempt${attempt.regressed ? " is-regression" : ""}${
                index === shownAttempts.length - 1 ? " is-final" : ""
              }`}
            >
              <span className="mini-image-wrap">
                <img src={attempt.image} alt="" />
                <small>{attempt.action === "generate" ? "GEN" : "EDIT"}</small>
              </span>
              <span className="mini-score">
                <small>{attempt.id}</small>
                <strong>
                  {attempt.passed}/{trajectory.totalAtoms}
                </strong>
              </span>
            </span>
            {index < shownAttempts.length - 1 && (
              <ArrowRight className="mini-arrow" size={15} aria-hidden="true" />
            )}
          </span>
        ))}
      </span>

      <span className="card-copy">
        <strong>{trajectory.title}</strong>
        <small>{trajectory.summary}</small>
      </span>
      <span className="card-link">
        完整轨迹 <ArrowRight size={14} aria-hidden="true" />
      </span>
    </button>
  );
}

function AttemptStrip({ trajectory }: { trajectory: Trajectory }) {
  return (
    <div
      className="attempt-grid"
      style={{ "--attempt-count": trajectory.attempts.length } as CSSProperties}
    >
      {trajectory.attempts.map((attempt, index) => {
        const isLast = index === trajectory.attempts.length - 1;
        const isRegression = Boolean(attempt.regressed);

        return (
          <article
            className={`attempt-item${isRegression ? " is-regression" : ""}${
              isLast ? " is-final" : ""
            }`}
            key={attempt.id}
          >
            <div className="attempt-image-wrap">
              <img
                src={attempt.image}
                alt={`${attempt.id}，${attempt.passed}/${trajectory.totalAtoms} 原子通过`}
                className="attempt-image"
              />
              <span className="attempt-action">
                {attempt.action === "generate" ? "GENERATE" : "EDIT"}
              </span>
            </div>
            <div className="attempt-heading">
              <span>{attempt.id}</span>
              <strong>
                {attempt.passed}/{trajectory.totalAtoms}
              </strong>
            </div>
            <div
              className="atom-track"
              aria-label={`${attempt.passed} / ${trajectory.totalAtoms} 原子通过`}
            >
              <span style={{ width: `${(attempt.passed / trajectory.totalAtoms) * 100}%` }} />
            </div>
            <p>{attempt.note}</p>
            <div className="attempt-meta">
              {attempt.parent && (
                <span>
                  {attempt.parent !== trajectory.attempts[index - 1]?.id && (
                    <GitBranch size={13} aria-hidden="true" />
                  )}
                  from {attempt.parent}
                </span>
              )}
              {attempt.fixed && (
                <span className="meta-fixed">
                  <Check size={13} aria-hidden="true" /> {attempt.fixed}
                </span>
              )}
              {attempt.regressed && (
                <span className="meta-regressed">
                  <RotateCcw size={13} aria-hidden="true" /> {attempt.regressed}
                </span>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}

export default function Home() {
  const [selectedId, setSelectedId] = useState(trajectories[0].id);
  const [filter, setFilter] = useState<FilterId>("all");
  const [batch, setBatch] = useState(0);
  const batchSize = 4;

  const filteredTrajectories = useMemo(
    () =>
      filter === "all"
        ? trajectories
        : trajectories.filter((item) => item.dimensions.includes(filter)),
    [filter],
  );
  const batchCount = Math.max(1, Math.ceil(filteredTrajectories.length / batchSize));
  const visibleTrajectories = filteredTrajectories.slice(
    batch * batchSize,
    batch * batchSize + batchSize,
  );
  const trajectory = useMemo(
    () => trajectories.find((item) => item.id === selectedId) ?? trajectories[0],
    [selectedId],
  );
  const first = trajectory.attempts[0];
  const last = trajectory.attempts[trajectory.attempts.length - 1];
  const gain = last.passed - first.passed;

  function selectTrajectory(id: string) {
    setSelectedId(id);
    window.requestAnimationFrame(() => {
      document.getElementById("trajectory")?.scrollIntoView({ behavior: "smooth" });
    });
  }

  function selectFilter(nextFilter: FilterId) {
    setFilter(nextFilter);
    setBatch(0);
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Gen-Retry 轨迹档案首页">
          <span className="brand-mark">GR</span>
          <span>GEN-RETRY</span>
        </a>
        <nav aria-label="页面导航">
          <a href="#explorer">轨迹浏览</a>
          <a href="#trajectory">完整轨迹</a>
          <a href="#prompt-diff">Prompt 变化</a>
          <a href="#evidence">总体证据</a>
        </nav>
        <span className="header-status">
          <i /> 200 TRAJECTORIES
        </span>
      </header>

      <section className="explorer" id="explorer">
        <div className="explorer-heading" id="top">
          <div>
            <span className="eyebrow">VERIFIER-GROUNDED IMAGE RETRY</span>
            <h1>看见 Retry 如何改对一张图</h1>
            <p>
              从计数、属性到空间关系与历史恢复，并排查看失败原子、动作选择与最终改善。
            </p>
          </div>
          <div className="archive-stats" aria-label="轨迹档案摘要">
            <span>
              <strong>8</strong>
              <small>典型轨迹</small>
            </span>
            <span>
              <strong>5</strong>
              <small>失败维度</small>
            </span>
            <span>
              <strong>+21</strong>
              <small>展示原子净增</small>
            </span>
          </div>
        </div>

        <div className="browser-toolbar">
          <div className="dimension-filters" aria-label="按失败维度筛选">
            {filters.map((item) => (
              <button
                type="button"
                className={filter === item.id ? "is-active" : ""}
                onClick={() => selectFilter(item.id)}
                aria-pressed={filter === item.id}
                key={item.id}
              >
                {item.label}
                <small>
                  {item.id === "all"
                    ? trajectories.length
                    : trajectories.filter((trajectoryItem) =>
                        trajectoryItem.dimensions.includes(item.id as TrajectoryDimension),
                      ).length}
                </small>
              </button>
            ))}
          </div>

          <div className="batch-controls">
            <span>
              {String(batch * batchSize + 1).padStart(2, "0")}–
              {String(Math.min((batch + 1) * batchSize, filteredTrajectories.length)).padStart(
                2,
                "0",
              )}{" "}
              / {String(filteredTrajectories.length).padStart(2, "0")}
            </span>
            <button
              type="button"
              onClick={() => setBatch((current) => Math.max(0, current - 1))}
              disabled={batch === 0}
              aria-label="上一批轨迹"
              title="上一批"
            >
              <ChevronLeft size={18} aria-hidden="true" />
            </button>
            <button
              type="button"
              onClick={() => setBatch((current) => Math.min(batchCount - 1, current + 1))}
              disabled={batch >= batchCount - 1}
              aria-label="下一批轨迹"
              title="下一批"
            >
              <ChevronRight size={18} aria-hidden="true" />
            </button>
          </div>
        </div>

        <div className="trajectory-gallery" aria-live="polite">
          {visibleTrajectories.map((item) => (
            <TrajectoryCard
              trajectory={item}
              selected={item.id === selectedId}
              onSelect={() => selectTrajectory(item.id)}
              key={item.id}
            />
          ))}
        </div>
      </section>

      <section className="trajectory-section" id="trajectory" aria-live="polite">
        <div className="detail-heading">
          <div className="detail-title">
            <span>{trajectory.index}</span>
            <div>
              <small>{trajectory.category}</small>
              <h2>{trajectory.title}</h2>
              <p>{trajectory.summary}</p>
            </div>
          </div>
          <div className="detail-metrics">
            <span>
              <small>ATOMS</small>
              <strong>
                {first.passed} <ArrowRight size={17} aria-hidden="true" /> {last.passed}
                <i>/{trajectory.totalAtoms}</i>
              </strong>
            </span>
            <span>
              <small>GAIN</small>
              <strong className="metric-positive">+{gain}</strong>
            </span>
            <span>
              <small>ATTEMPTS</small>
              <strong>{trajectory.attempts.length}</strong>
            </span>
          </div>
        </div>
        <AttemptStrip trajectory={trajectory} />
      </section>

      <section className="prompt-section" id="prompt-diff">
        <div className="section-intro prompt-intro">
          <div>
            <span className="section-number">02 / PROMPT EVOLUTION</span>
            <h2>从任务描述，到局部可执行指令</h2>
          </div>
          <blockquote>
            <span>ORIGINAL PROMPT</span>“{trajectory.originalPrompt}”
          </blockquote>
        </div>

        <div className="delta-row">
          {trajectory.promptDelta.map((delta) => (
            <DeltaChip delta={delta} key={delta.text} />
          ))}
        </div>

        <div className="prompt-grid">
          <article className="prompt-panel prompt-initial">
            <header>
              <span>INITIAL EXECUTION PROMPT</span>
              <strong>{first.id}</strong>
            </header>
            <PromptParagraphs text={trajectory.initialInstruction} />
          </article>
          <div className="prompt-arrow" aria-hidden="true">
            <ArrowRight size={22} />
          </div>
          <article className="prompt-panel prompt-retry">
            <header>
              <span>FINAL RETRY PROMPT</span>
              <strong>{last.id}</strong>
            </header>
            <PromptParagraphs text={trajectory.retryInstruction} />
          </article>
        </div>
      </section>

      <section className="evidence-section" id="evidence">
        <div className="evidence-heading">
          <span className="section-number">03 / AGGREGATE EVIDENCE</span>
          <h2>典型案例之外，200 条轨迹的整体结果</h2>
          <p>同一批 official-atomicity-matched prompts，Agent 从首轮结果提升到历史最优提交。</p>
        </div>
        <div className="evidence-metrics">
          <div>
            <span>SUBMITTED ATOMS</span>
            <strong>1,301</strong>
            <small>of 1,419 · +142 vs first attempt</small>
          </div>
          <div>
            <span>ALL-PASS TRAJECTORIES</span>
            <strong>111</strong>
            <small>of 200 prompts</small>
          </div>
          <div>
            <span>SOFT-TIFA GM</span>
            <strong>73.50</strong>
            <small>vs 31.53 paired Best-of-5 baseline</small>
          </div>
          <div>
            <span>IMAGE CALLS</span>
            <strong>684</strong>
            <small>vs 1,000 baseline calls</small>
          </div>
        </div>
        <div className="evidence-note">
          <ShieldCheck size={18} aria-hidden="true" />
          <p>
            这是集成系统证据，不是 compute-normalized 的策略因果消融。页面中的图片、动作、
            pass count 与分支均来自 immutable events 派生的 canonical episode state。
          </p>
        </div>
      </section>

      <footer>
        <span>GEN-RETRY / TRAJECTORY ARCHIVE</span>
        <span>Verifier-grounded · Image-aware · History-aware</span>
      </footer>
    </main>
  );
}
