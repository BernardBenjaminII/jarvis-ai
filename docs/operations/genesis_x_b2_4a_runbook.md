# Genesis X-B2.4A Runbook

Verify:

    ./dev/verify_genesis_x_b2_4a.sh

Inspect quality ranking:

    python -m dev.run_genesis_x_b2_4a quality \
      --query "How do C++ iterators work?" \
      --top-k 8 \
      --candidate-pool 60 \
      --scan-limit 25000

Deterministic grounded answer:

    python -m dev.run_genesis_x_b2_4a answer \
      --query "How do C++ iterators work?" \
      --top-k 8 \
      --candidate-pool 60 \
      --scan-limit 25000

Certification:

    python -m dev.run_genesis_x_b2_4a certify
