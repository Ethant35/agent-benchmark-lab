# Security
Author: Ethan

Run untrusted generated code only through the Docker/Podman execution boundary. There is no host-execution fallback. Keep the runtime, kernel and base image patched. Containers reduce exposure; they do not prove immunity from kernel or container-runtime vulnerabilities. For hostile workloads, use a disposable dedicated machine/VM with no valuable data.

No host home or credential mounts are made. Container networking is disabled, root filesystem is read-only, capabilities are dropped, privilege escalation is denied, and CPU/memory/process/runtime limits apply. Agent workspaces and hidden verifier volumes are separate. Candidate programs run unprivileged during verification. The host's provider API key is transmitted only to the configured endpoint and is not passed to tools. Configure only endpoints you trust. Never commit credentials or result traces containing private task inputs.

The local dashboard binds to 127.0.0.1, accepts loopback Host headers, exposes read-only APIs and does not enable cross-origin access. It has no remote authentication; do not proxy it onto a public network. React escapes evidence text; generated HTML reports escape JSON. CSV formula prefixes are neutralized.

Task bundles and reference actions are trusted operator code. Review third-party tasks before installation. The corpus is public; hidden verifier isolation is a runtime property, not protection against training contamination or an operator deliberately inspecting source.

A SIGKILL or machine failure can prevent cleanup. Resume the run to reconcile it. Inspect `podman ps -a --filter label=abl.managed=true` and remove only this project's abandoned resources. Preserve trial evidence before manual cleanup. Workspace archives are untrusted and may contain symlinks; the program never extracts them on the host.

Report security problems privately through the repository's GitHub security reporting channel when available; otherwise contact the repository owner without publishing exploit credentials or private data.
