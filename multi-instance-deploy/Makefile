# Makefile — Agent Matrix Fleet Release Builder (Phase 9)
#
# Builds a reproducible, deterministic release bundle containing all Phase 1-8
# runtime artifacts with a SHA-256 checksum manifest and zero embedded secrets.
#
# Usage:
#   make release VERSION=v1.2.0
#   make verify-reproducible VERSION=v1.2.0

SHELL := /usr/bin/env bash
VERSION ?= v1.2.0
RELEASE_DIR ?= /opt/agent-zero/releases
BUNDLE_PATH := $(RELEASE_DIR)/am-release-$(VERSION).tar.gz

ARTIFACTS := \
	templates/matrix-bot/matrix-bot-rust \
	templates/matrix-bot/run-bot-wrapper.sh \
	templates/matrix-bot/run-matrix-bot.sh \
	templates/scripts/derive-a0-token.sh \
	templates/scripts/preflight-check.sh \
	templates/scripts/watchdog.sh \
	templates/scripts/startup-services.sh

.PHONY: release verify-reproducible clean

release:
	@python3 scripts/build-release.py --version "$(VERSION)" --output "$(BUNDLE_PATH)"

verify-reproducible:
	@python3 scripts/build-release.py --version "$(VERSION)" --output "/tmp/am-release-repro-1.tar.gz"
	@python3 scripts/build-release.py --version "$(VERSION)" --output "/tmp/am-release-repro-2.tar.gz"
	@H1=$$(sha256sum /tmp/am-release-repro-1.tar.gz | awk '{print $$1}'); \
	 H2=$$(sha256sum /tmp/am-release-repro-2.tar.gz | awk '{print $$1}'); \
	 echo "Build 1 SHA-256: $$H1"; \
	 echo "Build 2 SHA-256: $$H2"; \
	 rm -f /tmp/am-release-repro-1.tar.gz /tmp/am-release-repro-2.tar.gz; \
	 test "$$H1" = "$$H2" && echo "REPRODUCIBLE BUILD VERIFIED ($$H1)"
