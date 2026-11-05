#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="repo-spec-audit"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SKILL_FILE="${SCRIPT_DIR}/SKILL.md"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Install or export the '${SKILL_NAME}' skill across agent harnesses.

Options:
  --global              Install into global user directories for Cursor (~/.cursor/skills),
                        Claude Code (~/.claude/skills & ~/.claude/commands), and Codex (~/.codex/skills)
                        (Default if no flags are provided)
  --project <PATH>      Install into a specific repository's .cursor/skills/ and .claude/commands/
  --package [OUT_DIR]   Create a portable '${SKILL_NAME}.tar.gz' archive (default: ${SCRIPT_DIR})
  --help                Show this help message
EOF
}

if [[ ! -f "${SKILL_FILE}" ]]; then
    echo "ERROR: Required file not found: ${SKILL_FILE}" >&2
    exit 1
fi

install_global() {
    echo "Installing ${SKILL_NAME} globally..."

    # 1. Cursor (~/.cursor/skills/repo-spec-audit/SKILL.md)
    local cursor_dir="${HOME}/.cursor/skills/${SKILL_NAME}"
    mkdir -p "${cursor_dir}"
    if [[ "${SCRIPT_DIR}" != "${cursor_dir}" ]]; then
        cp "${SKILL_FILE}" "${cursor_dir}/SKILL.md"
    fi
    echo "  [OK] Cursor:      ${cursor_dir}/SKILL.md"

    # 2. Claude Code (~/.claude/skills/repo-spec-audit/SKILL.md & ~/.claude/commands/repo-spec-audit.md)
    local claude_skill_dir="${HOME}/.claude/skills/${SKILL_NAME}"
    local claude_cmd_dir="${HOME}/.claude/commands"
    mkdir -p "${claude_skill_dir}" "${claude_cmd_dir}"
    cp "${SKILL_FILE}" "${claude_skill_dir}/SKILL.md"
    cp "${SKILL_FILE}" "${claude_cmd_dir}/${SKILL_NAME}.md"
    echo "  [OK] Claude Code: ${claude_skill_dir}/SKILL.md"
    echo "  [OK] Claude Cmd:  ${claude_cmd_dir}/${SKILL_NAME}.md"

    # 3. Codex / OpenCode (~/.codex/skills/repo-spec-audit/SKILL.md)
    local codex_dir="${HOME}/.codex/skills/${SKILL_NAME}"
    mkdir -p "${codex_dir}"
    cp "${SKILL_FILE}" "${codex_dir}/SKILL.md"
    echo "  [OK] Codex CLI:   ${codex_dir}/SKILL.md"
}

install_project() {
    local target_repo="$1"
    if [[ ! -d "${target_repo}" ]]; then
        echo "ERROR: Target project directory does not exist: ${target_repo}" >&2
        exit 2
    fi
    target_repo="$(cd -- "${target_repo}" && pwd)"
    echo "Installing ${SKILL_NAME} into project: ${target_repo}"

    mkdir -p "${target_repo}/.cursor/skills/${SKILL_NAME}"
    cp "${SKILL_FILE}" "${target_repo}/.cursor/skills/${SKILL_NAME}/SKILL.md"
    echo "  [OK] ${target_repo}/.cursor/skills/${SKILL_NAME}/SKILL.md"

    mkdir -p "${target_repo}/.claude/commands"
    cp "${SKILL_FILE}" "${target_repo}/.claude/commands/${SKILL_NAME}.md"
    echo "  [OK] ${target_repo}/.claude/commands/${SKILL_NAME}.md"
}

package_archive() {
    local out_dir="${1:-${SCRIPT_DIR}}"
    mkdir -p "${out_dir}"
    local archive_path="${out_dir}/${SKILL_NAME}.tar.gz"
    tar -czf "${archive_path}" -C "$(dirname "${SCRIPT_DIR}")" "${SKILL_NAME}/SKILL.md" "${SKILL_NAME}/install.sh"
    echo "  [OK] Packaged portable archive: ${archive_path}"
}

if [[ $# -eq 0 ]]; then
    install_global
    exit 0
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --global)
            install_global
            shift
            ;;
        --project)
            if [[ $# -lt 2 ]]; then
                echo "ERROR: --project requires a path argument" >&2
                exit 2
            fi
            install_project "$2"
            shift 2
            ;;
        --package)
            if [[ $# -ge 2 && "$2" != --* ]]; then
                package_archive "$2"
                shift 2
            else
                package_archive "${SCRIPT_DIR}"
                shift
            fi
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done
