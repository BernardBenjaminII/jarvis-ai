
window.__JARVIS_BOUNTY_UI_VERSION__ = "R9.6C-runtime-1";
(() => {
  "use strict";
  let host = null;
  const esc = value => String(value ?? "").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#39;");
  // JARVIS R8.6 — session-bound mission review
  let selectedSessionId = null;
  let reviewRequestGeneration = 0;

  async function api(path, options={}) {
    const response = await fetch(path,{cache:"no-store",credentials:"same-origin",...options,headers:{"Accept":"application/json","Content-Type":"application/json",...(options.headers||{})}});
    const payload = await response.json().catch(()=>({}));
    if(!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
    return payload;
  }
  function shell() {
    host.innerHTML = `<button class="jarvis-workspace-close" type="button">← Return to chat</button><main class="jarvis-bounty-agent"><header class="jba-header"><div><small>KALI · HUMAN-GATED AUTONOMOUS RECON</small><h1>Bug Bounty Agent</h1></div><button id="jba-refresh" type="button">Refresh</button></header><section class="jba-safety"><strong>Operating rule:</strong> Jarvis may automate only capabilities already authorized by the active R5 scope. Deeper investigation, validation and submission remain human-gated.</section><section class="jba-start"><h2>Start Authorized Recon</h2><div class="jba-start-grid"><label>Authorization ID<input id="jba-auth" autocomplete="off"></label><label>Root target<input id="jba-target" placeholder="example.com" autocomplete="off"></label><label>Budget<input id="jba-budget" type="number" min="1" max="1000" value="100"></label><button id="jba-create" type="button">Create Mission</button></div><p class="jba-help">This accepts only an existing live R5 authorization. Creating a mission does not expand scope.</p></section><section><div class="jba-section-head"><h2>Sessions</h2><span id="jba-status"></span></div><div id="jba-sessions"></div></section><section id="jba-detail" hidden></section></main>`;
    host.querySelector(".jarvis-workspace-close").onclick=()=>window.JARVIS_WORKSPACES?.close();
    host.querySelector("#jba-refresh").onclick=loadSessions;
    host.querySelector("#jba-create").onclick=createSession;
  }
  async function createSession() {
    const button=host.querySelector("#jba-create"), authorization_id=host.querySelector("#jba-auth").value.trim(), root_target=host.querySelector("#jba-target").value.trim(), budget=Number(host.querySelector("#jba-budget").value||100);
    if(!authorization_id||!root_target){alert("Authorization ID and root target are required.");return;}
    button.disabled=true;
    try{const out=await api("/api/bounty-agent/sessions",{method:"POST",body:JSON.stringify({authorization_id,root_target,budget})});await loadSessions();await showSession(out.session_id);}catch(error){alert(error.message);}finally{button.disabled=false;}
  }
  async function runSession(id) {
    const status=host.querySelector("#jba-status");status.textContent="Recon running…";
    try{await api(`/api/bounty-agent/sessions/${encodeURIComponent(id)}/run`,{method:"POST"});await loadSessions();await showSession(id);}catch(error){alert(error.message);await loadSessions();await showSession(id);}finally{status.textContent="";}
  }
  async function reviewCapabilityPolicy(
    planId,
    actionId,
    hypothesisId,
    decision,
    sessionId
  ) {
    const reviewer =
      window.prompt(
        `Reviewer identity for policy ${decision}:`
      );

    if (!reviewer) {
      return;
    }

    const policySource =
      window.prompt(
        "Policy source / URL / document reference:"
      );

    if (!policySource) {
      return;
    }

    const policyEvidence =
      window.prompt(
        "Policy evidence or reviewed rule supporting this decision:"
      );

    if (!policyEvidence) {
      return;
    }

    const constraintText =
      window.prompt(
        "Constraints, comma-separated (optional):",
        ""
      );

    const constraints =
      constraintText
        ? constraintText
            .split(",")
            .map(x => x.trim())
            .filter(Boolean)
        : [];

    try {
      await api(
        `/api/bounty-agent/investigation-plans/${
          encodeURIComponent(planId)
        }/actions/${
          encodeURIComponent(actionId)
        }/hypotheses/${
          encodeURIComponent(hypothesisId)
        }/capability-policy-review`,
        {
          method: "POST",
          body: JSON.stringify({
            reviewer,
            decision,
            policy_source: policySource,
            policy_evidence: policyEvidence,
            constraints,
          }),
        }
      );

      await showSession(sessionId);
    } catch (error) {
      alert(error.message);
    }
  }

  async function buildValidationAuthorizationProposal(
    planId,
    actionId,
    hypothesisId,
    sessionId
  ) {
    const reviewer =
      window.prompt(
        "Reviewer identity for validation authorization proposal:"
      );

    if (!reviewer) {
      return;
    }

    try {
      await api(
        `/api/bounty-agent/investigation-plans/${
          encodeURIComponent(planId)
        }/actions/${
          encodeURIComponent(actionId)
        }/hypotheses/${
          encodeURIComponent(hypothesisId)
        }/validation-authorization-proposal`,
        {
          method: "POST",
          body: JSON.stringify({
            reviewer,
            request_budget: 10,
            ttl: 1800,
          }),
        }
      );

      await showSession(sessionId);
    } catch (error) {
      alert(error.message);
    }
  }

  async function decideHypothesis(
    planId,
    actionId,
    hypothesisId,
    decision,
    sessionId
  ) {
    const reviewer =
      window.prompt(
        `Reviewer identity for ${decision}:`
      );

    if (!reviewer) {
      return;
    }

    try {
      await api(
        `/api/bounty-agent/investigation-plans/${
          encodeURIComponent(planId)
        }/actions/${
          encodeURIComponent(actionId)
        }/hypotheses/${
          encodeURIComponent(hypothesisId)
        }/decision`,
        {
          method: "POST",
          body: JSON.stringify({
            decision,
            reviewer,
          }),
        }
      );

      await showSession(sessionId);
    } catch (error) {
      alert(error.message);
    }
  }

  async function reviewActionEvidence(
    planId,
    actionId,
    sessionId
  ) {
    const reviewer =
      window.prompt(
        "Reviewer identity for evidence review:"
      );

    if (!reviewer) {
      return;
    }

    try {
      await api(
        `/api/bounty-agent/investigation-plans/${
          encodeURIComponent(planId)
        }/actions/${
          encodeURIComponent(actionId)
        }/evidence-review`,
        {
          method: "POST",
          body: JSON.stringify({
            reviewer,
          }),
        }
      );

      await showSession(sessionId);
    } catch (error) {
      alert(error.message);
    }
  }

  async function buildActionProposal(
    planId,
    actionId,
    sessionId
  ) {
    const reviewer =
      window.prompt(
        "Reviewer identity for proposal:"
      );

    if (!reviewer) {
      return;
    }

    try {
      await api(
        `/api/bounty-agent/investigation-plans/${
          encodeURIComponent(planId)
        }/actions/${
          encodeURIComponent(actionId)
        }/proposal`,
        {
          method: "POST",
          body: JSON.stringify({
            reviewer,
          }),
        }
      );

      await showSession(sessionId);
    } catch (error) {
      alert(error.message);
    }
  }

  async function planActionDecision(
    planId,
    actionId,
    value,
    sessionId
  ) {
    const reviewer =
      window.prompt(
        `Reviewer identity for ${value}:`
      );

    if (!reviewer) {
      return;
    }

    try {
      await api(
        `/api/bounty-agent/investigation-plans/${
          encodeURIComponent(planId)
        }/actions/${
          encodeURIComponent(actionId)
        }/decision`,
        {
          method: "POST",
          body: JSON.stringify({
            decision: value,
            reviewer,
          }),
        }
      );

      await showSession(sessionId);
    } catch (error) {
      alert(error.message);
    }
  }

  async function decision(optionId,value,sessionId) {
    const reviewer=window.prompt("Reviewer name for audit trail:","abdullah");if(!reviewer)return;
    try{await api(`/api/bounty-agent/options/${encodeURIComponent(optionId)}/decision`,{method:"POST",body:JSON.stringify({decision:value,reviewer})});await showSession(sessionId);await loadSessions();}catch(error){alert(error.message);}
  }
  async function loadSessions() {
    const target = host.querySelector("#jba-sessions");

    target.innerHTML =
      '<p class="jba-muted">Loading…</p>';

    try {
      const payload = await api(
        "/api/bounty-agent/sessions"
      );

      if (!payload.sessions.length) {
        target.innerHTML =
          '<p class="jba-muted">' +
          'No bounty-agent sessions yet.' +
          '</p>';
        return;
      }

      target.innerHTML = payload.sessions
        .map((s) => {
          const selected =
            s.id === selectedSessionId;

          return `
            <article
              class="jba-session${
                selected
                  ? " jba-session-selected"
                  : ""
              }"
              data-session-id="${esc(s.id)}"
              aria-current="${
                selected ? "true" : "false"
              }"
            >
              <div>
                <strong>${esc(s.program)}</strong>
                <span>${esc(s.root_target)}</span>

                <small class="jba-session-id">
                  ${esc(s.id)}
                </small>
              </div>

              <span class="jba-state">
                ${esc(s.state)}
              </span>

              <div class="jba-actions">
                ${
                  s.state === "authorized" ||
                  s.state === "failed"
                    ? `
                      <button
                        data-run="${esc(s.id)}"
                        type="button"
                      >
                        Run Recon
                      </button>
                    `
                    : ""
                }

                <button
                  data-view="${esc(s.id)}"
                  type="button"
                  aria-pressed="${
                    selected ? "true" : "false"
                  }"
                >
                  Review
                </button>
              </div>
            </article>
          `;
        })
        .join("");

      target
        .querySelectorAll("[data-run]")
        .forEach((button) => {
          button.onclick = () =>
            runSession(button.dataset.run);
        });

      target
        .querySelectorAll("[data-view]")
        .forEach((button) => {
          button.onclick = () =>
            showSession(button.dataset.view);
        });

    } catch (error) {
      target.innerHTML =
        `<p class="jba-error">${
          esc(error.message)
        }</p>`;
    }
  }

  async function showSession(id) {
    const section =
      host.querySelector("#jba-detail");

    /*
     * R8.6 stale-response protection.
     *
     * Only the newest selected session is allowed to
     * populate the mission-review pane.
     */
    selectedSessionId = id;

    const generation =
      ++reviewRequestGeneration;

    section.hidden = false;

    section.innerHTML = `
      <div class="jba-section-head">
        <div>
          <small>MISSION REVIEW · LOADING</small>
          <h2>${esc(id)}</h2>
        </div>

        <span class="jba-state">
          LOADING
        </span>
      </div>
    `;

    /*
     * R8.9.1:
     * Do not rebuild the Sessions list while Mission Review
     * is loading. Rebuilding the list changes document height
     * and can move the review panel away from the viewport.
     */
    try {
      const report = await api(
        `/api/bounty-agent/sessions/${
          encodeURIComponent(id)
        }`
      );

      /*
       * Request A may finish after the operator already
       * selected request B. In that case A is discarded.
       */
      if (
        generation !== reviewRequestGeneration ||
        selectedSessionId !== id
      ) {
        return;
      }

      /*
       * Backend identity must agree with the requested
       * session before anything is rendered.
       */
      if (
        !report.session ||
        report.session.id !== id
      ) {
        throw new Error(
          "Mission review response did not match " +
          "the selected session."
        );
      }

      const options =
        report.options || [];

      const investigationPlans =
        report.investigation_plans || [];

      const counts = {
        high: options.filter(
          (x) => x.priority === "high"
        ).length,

        medium: options.filter(
          (x) => x.priority === "medium"
        ).length,

        awaiting: options.filter(
          (x) => x.state === "awaiting_human"
        ).length,
      };

      const missionId =
        report.mission?.mission?.id ||
        report.session.mission ||
        "unknown";

      const missionTasks =
        report.mission?.tasks || [];

      const taskGroups = new Map();

      for (const task of missionTasks) {
        const target = task.target || "unknown";

        if (!taskGroups.has(target)) {
          taskGroups.set(target, []);
        }

        taskGroups.get(target).push(task);
      }

      const taskResult = (task) =>
        task?.evidence?.result || {};

      const dnsTasks = missionTasks.filter(
        (task) => task.capability === "dnsx"
      );

      const dnsResolvedCount = dnsTasks.filter(
        (task) => {
          const result = taskResult(task);

          return (
            result.state === "completed" &&
            result.returncode === 0 &&
            (result.accepted || []).includes(
              task.target
            )
          );
        }
      ).length;

      const pipelineTargets = Array.from(
        taskGroups.keys()
      ).sort();

      const renderStage = (
        label,
        provider,
        state,
        detail=""
      ) => `
        <div class="jba-pipeline-stage">
          <small>${esc(label)}</small>
          <strong>${esc(provider || "—")}</strong>
          <span>${esc(state)}</span>
          ${
            detail
              ? `<code>${esc(detail)}</code>`
              : ""
          }
        </div>
      `;

      /*
       * R9.2B — Human Pursuit Plan UI
       *
       * Plans are display-only here.
       * No action approval or execution controls exist
       * in this revision.
       */
      const renderPlanAction = (
        action,
        planId
      ) => {
        const approvalState =
          action.approval_state ||
          "not_approved";

        return `
          <article class="jba-plan-action">
            <div class="jba-plan-action-head">
              <strong>
                ${esc(
                  action.action ||
                  "Unnamed action"
                )}
              </strong>

              <span class="jba-plan-lock">
                ${esc(
                  approvalState === "approved"
                    ? "APPROVED · EXECUTION LOCKED"
                    : approvalState === "rejected"
                      ? "REJECTED"
                      : "NOT APPROVED"
                )}
              </span>
            </div>

            <div class="jba-plan-action-meta">
              <span>
                capability:
                <code>
                  ${esc(
                    action.capability_required ||
                    "human_review"
                  )}
                </code>
              </span>

              <span>
                state:
                <code>
                  ${esc(approvalState)}
                </code>
              </span>
            </div>

            ${
              action.rationale
                ? `
                    <p>
                      ${esc(action.rationale)}
                    </p>
                  `
                : ""
            }

            ${
              action.reviewer
                ? `
                    <div class="jba-plan-review">
                      reviewed by
                      <strong>
                        ${esc(action.reviewer)}
                      </strong>
                    </div>
                  `
                : ""
            }

            ${
              approvalState === "approved" &&
              !action.execution_proposal
                ? `
                    <div class="jba-plan-proposal-control">
                      <button
                        data-build-action-proposal
                        data-plan-id="${esc(planId)}"
                        data-action-id="${esc(action.id)}"
                      >
                        Build Proposal
                      </button>
                    </div>
                  `
                : ""
            }

            ${
              action.execution_proposal &&
              action.execution_proposal.proposal_state ===
                "ready_for_manual_review" &&
              !action.evidence_review
                ? `
                    <div class="jba-plan-review-control">
                      <button
                        data-review-action-evidence
                        data-plan-id="${esc(planId)}"
                        data-action-id="${esc(action.id)}"
                      >
                        Review Evidence
                      </button>
                    </div>
                  `
                : ""
            }

            ${
              action.execution_proposal
                ? `
                    <div class="jba-action-proposal">
                      <small>
                        R9.4 EXECUTION PROPOSAL
                      </small>

                      <strong>
                        ${esc(
                          action.execution_proposal
                            .proposal_state ||
                          "unknown"
                        )}
                      </strong>

                      <div>
                        capability:
                        <code>
                          ${esc(
                            action.execution_proposal
                              .capability_required ||
                            "unknown"
                          )}
                        </code>
                      </div>

                      <div>
                        capability authorized:
                        <code>
                          ${esc(
                            String(
                              action.execution_proposal
                                .capability_authorized
                            )
                          )}
                        </code>
                      </div>

                      <div>
                        new tool execution required:
                        <code>
                          ${esc(
                            String(
                              action.execution_proposal
                                .new_tool_execution_required
                            )
                          )}
                        </code>
                      </div>

                      <div>
                        execution allowed:
                        <code>
                          false
                        </code>
                      </div>

                      <p>
                        ${esc(
                          action.execution_proposal
                            .rationale || ""
                        )}
                      </p>
                    </div>
                  `
                : ""
            }

            ${
              action.evidence_review
                ? (() => {
                    const review =
                      action.evidence_review;

                    const observations =
                      review.observations || [];

                    const hypotheses =
                      review.hypotheses || [];

                    return `
                      <div class="jba-evidence-review">
                        <small>
                          R9.5 MANUAL EVIDENCE REVIEW
                        </small>

                        <strong>
                          ${esc(
                            review.classification ||
                            "unknown"
                          )}
                        </strong>

                        <div class="jba-evidence-review-status">
                          <span>
                            new network traffic:
                            <code>
                              ${esc(
                                String(
                                  review.new_network_traffic
                                )
                              )}
                            </code>
                          </span>

                          <span>
                            execution allowed:
                            <code>
                              ${esc(
                                String(
                                  review.execution_allowed
                                )
                              )}
                            </code>
                          </span>
                        </div>

                        <div class="jba-evidence-review-section">
                          <small>OBSERVATIONS</small>

                          ${
                            observations.length
                              ? `
                                  <ul>
                                    ${
                                      observations.map(
                                        (item) =>
                                          `<li>${
                                            esc(
                                              item.fact ||
                                              item.kind ||
                                              "Observation"
                                            )
                                          }</li>`
                                      ).join("")
                                    }
                                  </ul>
                                `
                              : `
                                  <p class="jba-muted">
                                    No observations.
                                  </p>
                                `
                          }
                        </div>

                        <div class="jba-evidence-review-section">
                          <small>HYPOTHESES</small>

                          ${
                            hypotheses.length
                              ? hypotheses.map(
                                  (item) => `
                                    <article class="jba-hypothesis">
                                      <strong>
                                        ${esc(
                                          item.id ||
                                          "H?"
                                        )}
                                      </strong>

                                      <span>
                                        ${esc(
                                          item.statement ||
                                          ""
                                        )}
                                      </span>

                                      <code>
                                        ${esc(
                                          item.status ||
                                          "unvalidated"
                                        )}
                                        ·
                                        ${esc(
                                          item.confidence ||
                                          "unknown"
                                        )}
                                      </code>

                                      ${
                                        item.selection_state
                                          ? `
                                              <div
                                                class="jba-hypothesis-state"
                                              >
                                                ${esc(
                                                  item.selection_state
                                                )}
                                                ${
                                                  item.selected_by
                                                    ? ` · ${esc(
                                                        item.selected_by
                                                      )}`
                                                    : ""
                                                }
                                              </div>
                                            `
                                          : `
                                              <div
                                                class="jba-hypothesis-controls"
                                              >
                                                <button
                                                  data-hypothesis-decision="select"
                                                  data-plan-id="${esc(planId)}"
                                                  data-action-id="${esc(action.id)}"
                                                  data-hypothesis-id="${esc(item.id)}"
                                                >
                                                  Select
                                                </button>

                                                <button
                                                  data-hypothesis-decision="hold"
                                                  data-plan-id="${esc(planId)}"
                                                  data-action-id="${esc(action.id)}"
                                                  data-hypothesis-id="${esc(item.id)}"
                                                >
                                                  Hold
                                                </button>

                                                <button
                                                  data-hypothesis-decision="reject"
                                                  data-plan-id="${esc(planId)}"
                                                  data-action-id="${esc(action.id)}"
                                                  data-hypothesis-id="${esc(item.id)}"
                                                >
                                                  Reject
                                                </button>
                                              </div>
                                            `
                                      }

                                      ${
                                        item.selection_state ===
                                        "selected"
                                          ? `
                                              <div
                                                class="jba-validation-lock"
                                              >
                                                VALIDATION NOT AUTHORIZED
                                                <br>
                                                execution allowed:
                                                false
                                              </div>

                                              ${
                                                !item.validation_authorization_proposal
                                                  ? `
                                                      <div
                                                        class="jba-validation-proposal-control"
                                                      >
                                                        <button
                                                          data-build-validation-proposal
                                                          data-plan-id="${esc(planId)}"
                                                          data-action-id="${esc(action.id)}"
                                                          data-hypothesis-id="${esc(item.id)}"
                                                        >
                                                          Build Validation Authorization Proposal
                                                        </button>
                                                      </div>
                                                    `
                                                  : ""
                                              }

                                              ${
                                                item.validation_authorization_proposal
                                                  ? (() => {
                                                      const proposal =
                                                        item.validation_authorization_proposal;

                                                      return `
                                                        <div
                                                          class="jba-validation-proposal"
                                                        >
                                                          <small>
                                                            R9.7 VALIDATION AUTHORIZATION PROPOSAL
                                                          </small>

                                                          <strong>
                                                            ${esc(
                                                              proposal.proposal_state ||
                                                              "unknown"
                                                            )}
                                                          </strong>

                                                          <div>
                                                            capability:
                                                            <code>
                                                              ${esc(
                                                                proposal.required_capability ||
                                                                "unknown"
                                                              )}
                                                            </code>
                                                          </div>

                                                          <div>
                                                            parent capability authorized:
                                                            <code>
                                                              ${esc(
                                                                String(
                                                                  proposal.capability_authorized
                                                                )
                                                              )}
                                                            </code>
                                                          </div>

                                                          <div>
                                                            target:
                                                            <code>
                                                              ${esc(
                                                                proposal.target ||
                                                                ""
                                                              )}
                                                            </code>
                                                          </div>

                                                          <div>
                                                            methods:
                                                            <code>
                                                              ${esc(
                                                                (
                                                                  proposal.allowed_methods ||
                                                                  []
                                                                ).join(", ")
                                                              )}
                                                            </code>
                                                          </div>

                                                          <div>
                                                            request budget:
                                                            <code>
                                                              ${esc(
                                                                String(
                                                                  proposal.request_budget
                                                                )
                                                              )}
                                                            </code>
                                                          </div>

                                                          <div>
                                                            TTL:
                                                            <code>
                                                              ${esc(
                                                                String(
                                                                  proposal.ttl_seconds
                                                                )
                                                              )}s
                                                            </code>
                                                          </div>

                                                          <div>
                                                            validation authorized:
                                                            <code>
                                                              ${esc(
                                                                String(
                                                                  proposal.validation_authorized
                                                                )
                                                              )}
                                                            </code>
                                                          </div>

                                                          <div>
                                                            execution allowed:
                                                            <code>
                                                              ${esc(
                                                                String(
                                                                  proposal.execution_allowed
                                                                )
                                                              )}
                                                            </code>
                                                          </div>

                                                          ${
                                                            proposal.proposal_state ===
                                                            "parent_capability_authorization_required"
                                                              ? `
                                                                  <div
                                                                    class="jba-validation-warning"
                                                                  >
                                                                    PARENT CAPABILITY AUTHORIZATION REQUIRED
                                                                    <br>
                                                                    No validation may run until the required
                                                                    capability is explicitly reviewed and authorized.
                                                                  </div>

                                                                  ${
                                                                    !proposal.capability_policy_review
                                                                      ? `
                                                                          <div
                                                                            class="jba-policy-review-controls"
                                                                          >
                                                                            <button
                                                                              data-policy-review="permit"
                                                                              data-plan-id="${esc(planId)}"
                                                                              data-action-id="${esc(action.id)}"
                                                                              data-hypothesis-id="${esc(item.id)}"
                                                                            >
                                                                              Policy Permits
                                                                            </button>

                                                                            <button
                                                                              data-policy-review="deny"
                                                                              data-plan-id="${esc(planId)}"
                                                                              data-action-id="${esc(action.id)}"
                                                                              data-hypothesis-id="${esc(item.id)}"
                                                                            >
                                                                              Policy Denies
                                                                            </button>

                                                                            <button
                                                                              data-policy-review="unclear"
                                                                              data-plan-id="${esc(planId)}"
                                                                              data-action-id="${esc(action.id)}"
                                                                              data-hypothesis-id="${esc(item.id)}"
                                                                            >
                                                                              Policy Unclear
                                                                            </button>
                                                                          </div>
                                                                        `
                                                                      : ""
                                                                  }
                                                                `
                                                              : ""
                                                          }

                                                          ${
                                                            proposal.capability_policy_review
                                                              ? (() => {
                                                                  const policy =
                                                                    proposal.capability_policy_review;

                                                                  return `
                                                                    <div
                                                                      class="jba-policy-review"
                                                                    >
                                                                      <small>
                                                                        R9.7D CAPABILITY POLICY REVIEW
                                                                      </small>

                                                                      <strong>
                                                                        ${esc(
                                                                          policy.policy_state ||
                                                                          "unknown"
                                                                        )}
                                                                      </strong>

                                                                      <div>
                                                                        decision:
                                                                        <code>
                                                                          ${esc(
                                                                            policy.decision ||
                                                                            ""
                                                                          )}
                                                                        </code>
                                                                      </div>

                                                                      <div>
                                                                        capability:
                                                                        <code>
                                                                          ${esc(
                                                                            policy.required_capability ||
                                                                            ""
                                                                          )}
                                                                        </code>
                                                                      </div>

                                                                      <div>
                                                                        reviewed by:
                                                                        <code>
                                                                          ${esc(
                                                                            policy.reviewer ||
                                                                            ""
                                                                          )}
                                                                        </code>
                                                                      </div>

                                                                      <div>
                                                                        source:
                                                                        <code>
                                                                          ${esc(
                                                                            policy.policy_source ||
                                                                            ""
                                                                          )}
                                                                        </code>
                                                                      </div>

                                                                      <div>
                                                                        evidence:
                                                                        <span>
                                                                          ${esc(
                                                                            policy.policy_evidence ||
                                                                            ""
                                                                          )}
                                                                        </span>
                                                                      </div>

                                                                      ${
                                                                        (
                                                                          policy.constraints ||
                                                                          []
                                                                        ).length
                                                                          ? `
                                                                              <div>
                                                                                constraints:
                                                                                <ul>
                                                                                  ${
                                                                                    policy.constraints
                                                                                      .map(
                                                                                        x =>
                                                                                          `<li>${esc(x)}</li>`
                                                                                      )
                                                                                      .join("")
                                                                                  }
                                                                                </ul>
                                                                              </div>
                                                                            `
                                                                          : ""
                                                                      }

                                                                      <div
                                                                        class="jba-validation-warning"
                                                                      >
                                                                        POLICY REVIEW IS NOT EXECUTION AUTHORIZATION
                                                                        <br>
                                                                        validation authorized: false
                                                                        <br>
                                                                        execution allowed: false
                                                                      </div>
                                                                    </div>
                                                                  `;
                                                                })()
                                                              : ""
                                                          }
                                                        </div>
                                                      `;
                                                    })()
                                                  : ""
                                              }
                                            `
                                          : ""
                                      }
                                    </article>
                                  `
                                ).join("")
                              : `
                                  <p class="jba-muted">
                                    No hypotheses generated.
                                  </p>
                                `
                          }
                        </div>

                        <p>
                          ${esc(
                            review.conclusion || ""
                          )}
                        </p>
                      </div>
                    `;
                  })()
                : ""
            }

            ${
              approvalState === "not_approved"
                ? `
                    <div class="jba-plan-action-decision">
                      <button
                        data-plan-action-decision="approve"
                        data-plan-id="${esc(planId)}"
                        data-action-id="${esc(action.id)}"
                      >
                        Approve
                      </button>

                      <button
                        data-plan-action-decision="reject"
                        data-plan-id="${esc(planId)}"
                        data-action-id="${esc(action.id)}"
                      >
                        Reject
                      </button>
                    </div>
                  `
                : ""
            }
          </article>
        `;
      };

      const renderInvestigationPlan = (
        wrapper
      ) => {
        const plan =
          wrapper.plan || {};

        const basis =
          plan.evidence_basis || {};

        const actions =
          plan.proposed_actions || [];

        const reasons =
          basis.reasons || [];

        return `
          <article class="jba-investigation-plan">
            <div class="jba-section-head">
              <div>
                <small>
                  INVESTIGATION PLAN
                </small>

                <h3>
                  ${esc(
                    plan.target ||
                    wrapper.target ||
                    "unknown target"
                  )}
                </h3>
              </div>

              <span class="jba-state">
                ${esc(
                  plan.state ||
                  wrapper.state ||
                  "unknown"
                )}
              </span>
            </div>

            <div class="jba-plan-safety">
              Human pursuit selected.
              No deeper action is approved for execution.
            </div>

            <div class="jba-plan-basis">
              <div>
                <small>SCORE</small>
                <strong>
                  ${esc(
                    basis.score ?? "—"
                  )}
                </strong>
              </div>

              <div>
                <small>PRIORITY</small>
                <strong>
                  ${esc(
                    basis.priority || "—"
                  )}
                </strong>
              </div>

              <div>
                <small>RISK</small>
                <strong>
                  ${esc(
                    basis.risk || "—"
                  )}
                </strong>
              </div>

              <div>
                <small>REVIEWER</small>
                <strong>
                  ${esc(
                    plan.reviewer ||
                    wrapper.reviewer ||
                    "—"
                  )}
                </strong>
              </div>
            </div>

            ${
              reasons.length
                ? `
                    <div class="jba-plan-evidence">
                      <small>
                        EVIDENCE BASIS
                      </small>

                      <ul>
                        ${
                          reasons
                            .map(
                              (reason) =>
                                `<li>${
                                  esc(reason)
                                }</li>`
                            )
                            .join("")
                        }
                      </ul>
                    </div>
                  `
                : ""
            }

            ${
              basis.recommendation
                ? `
                    <p class="jba-plan-recommendation">
                      ${esc(
                        basis.recommendation
                      )}
                    </p>
                  `
                : ""
            }

            <div class="jba-plan-actions">
              <div class="jba-plan-actions-head">
                <small>
                  PROPOSED ACTIONS
                </small>

                <span>
                  ${actions.length}
                  awaiting approval
                </span>
              </div>

              ${
                actions.length
                  ? actions
                      .map(
                        (action) =>
                          renderPlanAction(
                            action,
                            wrapper.id
                          )
                      )
                      .join("")
                  : `
                      <p class="jba-muted">
                        No proposed actions.
                      </p>
                    `
              }
            </div>

            <div class="jba-plan-boundaries">
              <span>
                scope expansion:
                <strong>NO</strong>
              </span>

              <span>
                automatic execution:
                <strong>NO</strong>
              </span>

              <span>
                vulnerability validation:
                <strong>NO</strong>
              </span>

              <span>
                report submission:
                <strong>NO</strong>
              </span>
            </div>
          </article>
        `;
      };

      const renderTargetPipeline = (target) => {
        const tasks =
          taskGroups.get(target) || [];

        const discoveryTask = tasks.find(
          (task) =>
            task.capability === "subfinder"
        );

        const dnsTask = tasks.find(
          (task) =>
            task.capability === "dnsx"
        );

        const httpTask = tasks.find(
          (task) =>
            task.capability === "httpx"
        );

        const discoveryResult =
          taskResult(discoveryTask);

        const dnsResult =
          taskResult(dnsTask);

        const httpResult =
          taskResult(httpTask);

        let discoveryState = "not attempted";

        if (discoveryTask) {
          discoveryState =
            discoveryTask.state || "unknown";
        }

        let dnsState = "not attempted";
        let dnsDetail = "";

        if (dnsTask) {
          const accepted =
            dnsResult.accepted || [];

          const records =
            dnsResult.records || [];

          const addresses = [];

          for (const record of records) {
            const values =
              record.a ||
              record.A ||
              record.answers ||
              [];

            if (Array.isArray(values)) {
              for (const value of values) {
                addresses.push(
                  String(value)
                );
              }
            }
          }

          const resolved =
            dnsResult.state === "completed" &&
            dnsResult.returncode === 0 &&
            accepted.includes(target);

          dnsState =
            resolved
              ? "resolved"
              : "unresolved";

          dnsDetail = addresses.length
            ? `A ${[
                ...new Set(addresses)
              ].join(", ")}`
            : "";
        }

        let httpState = "not attempted";
        let httpDetail = "";

        if (httpTask) {
          httpState =
            httpTask.state || "unknown";

          const records =
            httpResult.records || [];

          const record =
            records[0] || {};

          const status =
            record.status_code ??
            httpResult.status_code;

          const title =
            record.title ??
            httpResult.title;

          httpDetail = [
            status
              ? `HTTP ${status}`
              : "",
            title || "",
          ]
            .filter(Boolean)
            .join(" · ");
        } else if (
          dnsTask &&
          dnsState === "unresolved"
        ) {
          httpState = "blocked by DNS gate";
        }

        return `
          <article class="jba-pipeline-target">
            <div class="jba-pipeline-target-head">
              <strong>${esc(target)}</strong>
            </div>

            <div class="jba-pipeline-stages">
              ${renderStage(
                "DISCOVERY",
                discoveryTask
                  ? "subfinder"
                  : "",
                discoveryState,
                discoveryResult.accepted
                  ? `${
                      discoveryResult
                        .accepted.length
                    } accepted`
                  : ""
              )}

              ${renderStage(
                "DNS",
                dnsTask ? "dnsx" : "",
                dnsState,
                dnsDetail
              )}

              ${renderStage(
                "HTTP",
                httpTask ? "httpx" : "",
                httpState,
                httpDetail
              )}
            </div>
          </article>
        `;
      };

      section.innerHTML = `
        <div class="jba-section-head">
          <div>
            <small>MISSION REVIEW</small>

            <h2>
              ${esc(report.session.program)}
              ·
              ${esc(report.session.root_target)}
            </h2>

            <div class="jba-review-identity">
              <span>
                SESSION
                <code>
                  ${esc(report.session.id)}
                </code>
              </span>

              <span>
                MISSION
                <code>
                  ${esc(missionId)}
                </code>
              </span>
            </div>
          </div>

          <span class="jba-state">
            ${esc(report.session.state)}
          </span>
        </div>

        <div class="jba-metrics">
          <div>
            <small>OPTIONS</small>
            <strong>${options.length}</strong>
          </div>

          <div>
            <small>HIGH</small>
            <strong>${counts.high}</strong>
          </div>

          <div>
            <small>MEDIUM</small>
            <strong>${counts.medium}</strong>
          </div>

          <div>
            <small>NEEDS YOU</small>
            <strong>${counts.awaiting}</strong>
          </div>
        </div>

        ${
          missionTasks.length
            ? `
              <section class="jba-pipeline">
                <div class="jba-section-head">
                  <div>
                    <small>MISSION PIPELINE</small>
                    <h3>Recon Evidence</h3>
                  </div>

                  <span class="jba-state">
                    ${
                      dnsTasks.length
                        ? `${dnsResolvedCount}/${dnsTasks.length} DNS resolved`
                        : "legacy path"
                    }
                  </span>
                </div>

                <div class="jba-pipeline-list">
                  ${
                    pipelineTargets
                      .map(
                        renderTargetPipeline
                      )
                      .join("")
                  }
                </div>
              </section>
            `
            : ""
        }

        ${
          investigationPlans.length
            ? `
                <section class="jba-investigation-plans">
                  <div class="jba-section-head">
                    <div>
                      <small>
                        HUMAN PURSUIT
                      </small>

                      <h3>
                        Investigation Plans
                      </h3>
                    </div>

                    <span class="jba-state">
                      ${investigationPlans.length}
                      active
                    </span>
                  </div>

                  <div class="jba-investigation-plan-list">
                    ${
                      investigationPlans
                        .map(
                          renderInvestigationPlan
                        )
                        .join("")
                    }
                  </div>
                </section>
              `
            : ""
        }

        <div class="jba-options">
          ${
            options.length
              ? options.map((o) => {
                  const a =
                    o.analysis || {};

                  return `
                    <article class="jba-option">
                      <div class="jba-score">
                        ${esc(o.score)}
                      </div>

                      <div class="jba-option-main">
                        <strong>
                          ${esc(o.target)}
                        </strong>

                        <span>
                          ${esc(o.priority)}
                          priority ·
                          ${esc(o.risk)}
                          decision gate
                        </span>

                        <ul>
                          ${
                            (a.reasons || [])
                              .map(
                                (r) =>
                                  `<li>${
                                    esc(r)
                                  }</li>`
                              )
                              .join("")
                          }
                        </ul>

                        <p>
                          ${esc(
                            a.recommendation || ""
                          )}
                        </p>
                      </div>

                      <div class="jba-decision">
                        <span>
                          ${esc(o.state)}
                        </span>

                        ${
                          o.state ===
                          "awaiting_human"
                            ? `
                              <button
                                data-decide="pursue"
                                data-option="${
                                  esc(o.id)
                                }"
                              >
                                Pursue
                              </button>

                              <button
                                data-decide="hold"
                                data-option="${
                                  esc(o.id)
                                }"
                              >
                                Hold
                              </button>

                              <button
                                data-decide="reject"
                                data-option="${
                                  esc(o.id)
                                }"
                              >
                                Reject
                              </button>
                            `
                            : ""
                        }
                      </div>
                    </article>
                  `;
                }).join("")
              : `
                <p class="jba-muted">
                  No analyzed options yet.
                </p>
              `
          }
        </div>
      `;

      section
        .querySelectorAll("[data-decide]")
        .forEach((button) => {
          button.onclick = () =>
            decision(
              button.dataset.option,
              button.dataset.decide,
              id
            );
        });

      section
        .querySelectorAll(
          "[data-policy-review]"
        )
        .forEach((button) => {
          button.onclick = () =>
            reviewCapabilityPolicy(
              button.dataset.planId,
              button.dataset.actionId,
              button.dataset.hypothesisId,
              button.dataset.policyReview,
              id
            );
        });

      section
        .querySelectorAll(
          "[data-build-validation-proposal]"
        )
        .forEach((button) => {
          button.onclick = () =>
            buildValidationAuthorizationProposal(
              button.dataset.planId,
              button.dataset.actionId,
              button.dataset.hypothesisId,
              id
            );
        });

      section
        .querySelectorAll(
          "[data-hypothesis-decision]"
        )
        .forEach((button) => {
          button.onclick = () =>
            decideHypothesis(
              button.dataset.planId,
              button.dataset.actionId,
              button.dataset.hypothesisId,
              button.dataset.hypothesisDecision,
              id
            );
        });

      section
        .querySelectorAll(
          "[data-review-action-evidence]"
        )
        .forEach((button) => {
          button.onclick = () =>
            reviewActionEvidence(
              button.dataset.planId,
              button.dataset.actionId,
              id
            );
        });

      section
        .querySelectorAll(
          "[data-build-action-proposal]"
        )
        .forEach((button) => {
          button.onclick = () =>
            buildActionProposal(
              button.dataset.planId,
              button.dataset.actionId,
              id
            );
        });

      section
        .querySelectorAll(
          "[data-plan-action-decision]"
        )
        .forEach((button) => {
          button.onclick = () =>
            planActionDecision(
              button.dataset.planId,
              button.dataset.actionId,
              button.dataset.planActionDecision,
              id
            );
        });

      /*
       * R8.9.1:
       * Keep the completed Mission Review visible.
       *
       * The previous implementation refreshed the Sessions
       * list first, which could move #jba-detail hundreds of
       * pixels and make Review appear to flash/disappear.
       */
      section.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });

      /*
       * Synchronize the session-list selection only after the
       * review has rendered and navigation has been anchored.
       */
      await loadSessions();

      /*
       * The list refresh can still slightly alter page height,
       * so anchor once more without animation.
       */
      section.scrollIntoView({
        behavior: "auto",
        block: "start",
      });

    } catch (error) {
      if (
        generation !== reviewRequestGeneration ||
        selectedSessionId !== id
      ) {
        return;
      }

      section.innerHTML =
        `<p class="jba-error">${
          esc(error.message)
        }</p>`;
    }
  }

  async function mount(target) {
    host = target;

    selectedSessionId = null;
    reviewRequestGeneration += 1;

    shell();
    await loadSessions();
  }
  window.JARVIS_BOUNTY_AGENT=Object.freeze({mount});
})();