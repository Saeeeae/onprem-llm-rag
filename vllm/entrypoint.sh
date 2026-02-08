#!/bin/bash
set -e

echo "Starting vLLM with configuration:"
echo "  Model: ${MODEL_NAME}"
echo "  Model Path: ${MODEL_PATH}"
echo "  Tensor Parallel Size: ${VLLM_TENSOR_PARALLEL_SIZE}"
echo "  GPU Memory Utilization: ${GPU_MEMORY_UTILIZATION}"
echo "  Max Model Length: ${MAX_MODEL_LEN}"
echo "  Max Sequences: ${MAX_NUM_SEQS:-256}"

python -m vllm.entrypoints.openai.api_server \
    --model "${MODEL_PATH}" \
    --tensor-parallel-size "${VLLM_TENSOR_PARALLEL_SIZE}" \
    --gpu-memory-utilization "${GPU_MEMORY_UTILIZATION}" \
    --max-model-len "${MAX_MODEL_LEN}" \
    --max-num-seqs "${MAX_NUM_SEQS:-256}" \
    --trust-remote-code \
    --host 0.0.0.0 \
    --port 8000
